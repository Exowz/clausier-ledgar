"""Fine-tune BERT classifiers with a hand-written PyTorch loop."""

import argparse
from contextlib import nullcontext
from pathlib import Path
from time import perf_counter

import matplotlib
import numpy as np
import torch
from torch.nn.utils import clip_grad_norm_
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from src.classification.dataset import make_loader, texts_to_dataset, tokenize_dataset
from src.classification.lora import count_parameters, inject_lora, merge_all_lora, training_memory_gb
from src.classification.metrics import evaluate
from src.classification.run_io import save_run
from src.data import get_label_names, load_split
from src.utils import ensure_dir, get_device, load_yaml, save_json, set_seed

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DEFAULTS: dict = {
    "run_name": "legal_bert", "model_type": "transformer", "model_name": "nlpaueb/legal-bert-base-uncased",
    "max_length": 256, "batch_size": 32, "eval_batch_size": 128, "lr": 3e-5,
    "weight_decay": 0.01, "epochs": 4, "warmup_ratio": 0.1, "grad_clip": 1.0,
    "patience": 1, "fp16": True, "log_every": 50, "num_workers": 2,
    "seed": 42, "device": None, "n_train": None, "use_lora": False,
    "lora_r": 8, "lora_alpha": 16, "lora_targets": ["query", "value"],
}


def load_config(path: str | Path, overrides: dict | None = None) -> dict:
    """Merge defaults, YAML configuration, and explicit overrides."""
    config = load_yaml(path)
    defaults = {} if config.get("model_type") == "lstm" else DEFAULTS
    return {**defaults, **config, **(overrides or {})}


def train_one_epoch(
    model, loader, optimizer, scheduler, device, scaler=None, grad_clip=1.0, log_every=50,
) -> tuple[float, list[float]]:
    """Train for one epoch and return the mean loss and block means."""
    model.train()
    optimizer.zero_grad()
    total_loss = 0.0
    total_examples = 0
    block_losses = []
    block_total = 0.0
    block_steps = 0
    for batch in loader:
        batch = {key: value.to(device) for key, value in batch.items()}
        context = torch.autocast("cuda", dtype=torch.float16) if scaler is not None else nullcontext()
        with context:
            loss = model(**batch).loss
        if scaler is None:
            loss.backward()
            clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
        else:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            clip_grad_norm_(model.parameters(), grad_clip)
            scaler.step(optimizer)
            scaler.update()
        scheduler.step()
        optimizer.zero_grad()
        if device.type == "mps":
            torch.mps.empty_cache()  # MPS keeps buffers per batch shape; dynamic padding fills memory otherwise
        loss_value = float(loss.detach())
        batch_size = len(batch["labels"])
        total_loss += loss_value * batch_size
        total_examples += batch_size
        block_total += loss_value
        block_steps += 1
        if block_steps == log_every:
            block_losses.append(block_total / block_steps)
            block_total = 0.0
            block_steps = 0
    if block_steps:
        block_losses.append(block_total / block_steps)
    return total_loss / total_examples, block_losses


def predict_loader(model, loader, device, fp16: bool = False) -> tuple[np.ndarray, np.ndarray, float]:
    """Return ordered probabilities, labels, and mean cross-entropy loss."""
    model.eval()
    probabilities = []
    labels = []
    total_loss = 0.0
    total_examples = 0
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            context = torch.autocast("cuda", dtype=torch.float16) if fp16 and device.type == "cuda" else nullcontext()
            with context:
                output = model(**batch)
            batch_size = len(batch["labels"])
            total_loss += float(output.loss) * batch_size
            total_examples += batch_size
            probabilities.append(torch.softmax(output.logits.float(), dim=-1).cpu().numpy())
            labels.append(batch["labels"].cpu().numpy())
            if device.type == "mps":
                torch.mps.empty_cache()
    return (np.concatenate(probabilities).astype(np.float32),
            np.concatenate(labels).astype(np.int64), total_loss / total_examples)


def fit(model, train_loader, val_loader, cfg: dict, device, label_names: list[str]) -> tuple[dict, list[dict]]:
    """Train with AdamW, linear warmup, and macro-F1 early stopping."""
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    total_steps = len(train_loader) * cfg["epochs"]
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=round(cfg["warmup_ratio"] * total_steps), num_training_steps=total_steps,
    )
    use_fp16 = bool(cfg["fp16"] and device.type == "cuda")
    scaler = torch.amp.GradScaler("cuda") if use_fp16 else None
    best_score = -1.0
    best_epoch = 0
    best_state = None
    history = []
    stale_epochs = 0
    for epoch in range(1, cfg["epochs"] + 1):
        start = perf_counter()
        train_loss, blocks = train_one_epoch(
            model, train_loader, optimizer, scheduler, device, scaler=scaler,
            grad_clip=cfg["grad_clip"], log_every=cfg["log_every"],
        )
        val_probs, val_labels, val_loss = predict_loader(model, val_loader, device, fp16=use_fp16)
        val_metrics = evaluate(val_probs, val_labels, label_names)
        row = {
            "epoch": epoch, "train_loss": train_loss, "train_loss_blocks": blocks,
            "val_loss": val_loss, "val_accuracy": val_metrics["accuracy"],
            "val_macro_f1": val_metrics["macro_f1"], "lr_end": scheduler.get_last_lr()[0],
            "epoch_time_s": perf_counter() - start,
        }
        history.append(row)
        print(
            f"[{cfg['run_name']}] epoch {epoch}: train loss {train_loss:.3f}, val loss {val_loss:.3f}, "
            f"val macro-F1 {row['val_macro_f1']:.3f} ({row['epoch_time_s']:.0f}s)", flush=True,
        )
        if row["val_macro_f1"] > best_score:
            best_score = row["val_macro_f1"]
            best_epoch = epoch
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= cfg["patience"]:
                break
    model.load_state_dict(best_state)
    return {"best_epoch": best_epoch, "best_val_macro_f1": best_score}, history


def plot_curves(history: list[dict], path: Path, title: str) -> None:
    """Plot epoch losses, block losses, and validation macro-F1."""
    epochs = [row["epoch"] for row in history]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(epochs, [row["train_loss"] for row in history], "o-", label="Train loss")
    axes[0].plot(epochs, [row["val_loss"] for row in history], "o-", label="Validation loss")
    block_x = []
    block_y = []
    for row in history:
        count = len(row["train_loss_blocks"])
        block_x.extend(row["epoch"] - 1 + (index + 0.5) / count for index in range(count))
        block_y.extend(row["train_loss_blocks"])
    axes[0].plot(block_x, block_y, linewidth=1, alpha=0.6, label="Train block loss")
    axes[0].set(xlabel="Epoch", ylabel="Cross-entropy loss", title="Training and validation loss")
    axes[0].legend()
    scores = [row["val_macro_f1"] for row in history]
    axes[1].plot(epochs, scores, "o-", label="Validation macro-F1")
    best_index = int(np.argmax(scores))
    axes[1].scatter([epochs[best_index]], [scores[best_index]], marker="*", s=180, label="Best epoch")
    axes[1].set(xlabel="Epoch", ylabel="Macro-F1", title="Validation macro-F1")
    axes[1].legend()
    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _truncated_share(texts: list[str], tokenizer, max_length: int) -> float:
    """Measure the share of training texts longer than max_length tokens."""
    truncated = 0
    for start in range(0, len(texts), 256):
        encoded = tokenizer(texts[start:start + 256], truncation=False, verbose=False)["input_ids"]
        truncated += sum(len(ids) > max_length for ids in encoded)
    return truncated / len(texts)


def run_training(
    cfg: dict, data: dict[str, tuple[list[str], np.ndarray]], label_names: list[str], output_dir: str | Path,
) -> dict:
    """Train, evaluate, and write a standard run with a reloadable model."""
    cfg = {**DEFAULTS, **cfg}
    set_seed(cfg["seed"])
    device = get_device(cfg["device"])
    print(f"Device: {device}", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(cfg["model_name"])
    id2label = dict(enumerate(label_names))
    label2id = {name: index for index, name in id2label.items()}
    model = AutoModelForSequenceClassification.from_pretrained(
        cfg["model_name"], num_labels=len(label_names), id2label=id2label, label2id=label2id,
    ).to(device)
    if cfg["use_lora"]:
        inject_lora(model, targets=tuple(cfg["lora_targets"]), r=cfg["lora_r"], alpha=cfg["lora_alpha"])
    trainable_params, total_params = count_parameters(model)
    workers = cfg["num_workers"] if device.type == "cuda" else 0
    loaders = {}
    for split in ("train", "validation", "test"):
        texts, labels = data[split]
        dataset = texts_to_dataset(texts, labels)
        tokenized = tokenize_dataset(dataset, tokenizer, cfg["max_length"])
        loaders[split] = make_loader(
            tokenized, tokenizer, cfg["batch_size"] if split == "train" else cfg["eval_batch_size"],
            shuffle=split == "train", seed=cfg["seed"], num_workers=workers,
        )
    print(f"Steps per epoch: {len(loaders['train'])}", flush=True)
    start = perf_counter()
    best_info, history = fit(model, loaders["train"], loaders["validation"], cfg, device, label_names)
    train_time_s = perf_counter() - start
    val_probs, val_labels, _ = predict_loader(model, loaders["validation"], device,
                                              fp16=cfg["fp16"] and device.type == "cuda")
    test_probs, test_labels, _ = predict_loader(model, loaders["test"], device,
                                                fp16=cfg["fp16"] and device.type == "cuda")
    run_dir = ensure_dir(Path(output_dir) / cfg["run_name"])
    run_config = {
        **cfg, "model_type": "transformer", "device": str(device), "n_train": len(data["train"][0]),
        "truncated_train_share": _truncated_share(data["train"][0], tokenizer, cfg["max_length"]),
        "best_epoch": best_info["best_epoch"], "trainable_params": trainable_params,
        "total_params": total_params,
        "train_memory_gb_estimate": training_memory_gb(total_params - trainable_params, trainable_params),
        "train_time_s": train_time_s,
    }
    metrics = save_run(run_dir, run_config, val_probs, val_labels, test_probs, test_labels, label_names)
    save_json(history, run_dir / "history.json")
    plot_curves(history, run_dir / "training_curves.png", cfg["run_name"])
    if cfg["use_lora"]:
        merge_all_lora(model)
    model.save_pretrained(run_dir / "model")
    tokenizer.save_pretrained(run_dir / "model")
    return metrics


def main(argv: list[str] | None = None) -> None:
    """Load LEDGAR, apply CLI overrides, and train one run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--run-name")
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"))
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--eval-batch-size", type=int)
    parser.add_argument("--lr", type=float)
    parser.add_argument("--max-length", type=int)
    parser.add_argument("--n-train", type=int)
    args = parser.parse_args(argv)
    overrides = {key: value for key, value in {
        "run_name": args.run_name, "device": args.device, "epochs": args.epochs,
        "batch_size": args.batch_size, "eval_batch_size": args.eval_batch_size, "lr": args.lr,
        "max_length": args.max_length,
        "n_train": args.n_train,
    }.items() if value is not None}
    cfg = load_config(args.config, overrides)
    if cfg["model_type"] == "lstm" and args.max_length is not None:
        cfg["max_tokens"] = args.max_length
        del cfg["max_length"]
    if args.smoke:
        cfg["n_train"] = args.n_train if args.n_train is not None else 2000
        cfg["epochs"] = 1
        cfg["run_name"] += "_smoke"
    data = {
        "train": load_split("train", n=cfg["n_train"], seed=cfg["seed"]),
        "validation": load_split("validation", n=500 if args.smoke else None, seed=cfg["seed"]),
        "test": load_split("test", n=500 if args.smoke else None, seed=cfg["seed"]),
    }
    if cfg["model_type"] == "lstm":
        from src.classification.lstm import run_training as run_lstm_training

        metrics = run_lstm_training(cfg, data, get_label_names(), args.output_dir)
    elif cfg["model_type"] == "transformer":
        metrics = run_training(cfg, data, get_label_names(), args.output_dir)
    else:
        raise ValueError(f"Unknown model_type: {cfg['model_type']}")
    for split in ("validation", "test"):
        result = metrics[split]
        print(f"{split}: accuracy={result['accuracy']:.4f}, macro-F1={result['macro_f1']:.4f}", flush=True)


if __name__ == "__main__":
    main()
