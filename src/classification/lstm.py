"""TP04 packed LSTM clause classifier for LEDGAR."""

import gzip
import re
from collections import Counter
from pathlib import Path
from time import perf_counter
from urllib.request import urlretrieve

import numpy as np
import torch
from torch import nn
from torch.nn.utils import clip_grad_norm_, rnn
from torch.utils.data import DataLoader, Dataset

from src.classification.metrics import evaluate
from src.classification.run_io import save_run
from src.utils import ensure_dir, load_json, resolve_path, save_json, set_seed

PAD, UNK = "<pad>", "<unk>"
PAD_ID, UNK_ID = 0, 1
GLOVE_URL = (
    "https://github.com/RaRe-Technologies/gensim-data/releases/download/"
    "glove-wiki-gigaword-50/glove-wiki-gigaword-50.gz"
)
GLOVE_PATH = "outputs/cache/glove/glove-wiki-gigaword-50.gz"


def tokenize(text: str) -> list[str]:
    """Return lowercase alphanumeric tokens using the TP04 regex."""
    return re.findall(r"[a-z0-9]+", text.lower())


def build_vocab(counts: Counter, min_freq: int = 2) -> list[str]:
    """Build a frequency-ordered vocabulary with stable alphabetic ties."""
    return [PAD, UNK] + [word for word, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
                         if count >= min_freq and word not in {PAD, UNK}]


def encode(text: str, stoi: dict[str, int]) -> list[int]:
    """Map regex tokens to vocabulary ids, using UNK for unseen words."""
    return [stoi.get(token, UNK_ID) for token in tokenize(text)]


class ClauseDataset(Dataset):
    """Store encoded clauses and integer labels for a PyTorch loader."""

    def __init__(self, texts: list[str], labels: np.ndarray, stoi: dict[str, int], max_tokens: int | None = None):
        """Encode clauses, truncate if requested, and retain one id for empty text."""
        self.ids = [torch.tensor((encode(text, stoi)[:max_tokens] or [UNK_ID]), dtype=torch.long) for text in texts]
        self.labels = np.asarray(labels, dtype=np.int64)

    def __len__(self) -> int:
        """Return the number of clauses."""
        return len(self.ids)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        """Return encoded ids and the matching label."""
        return self.ids[index], int(self.labels[index])


def collate_fn(batch: list[tuple[torch.Tensor, int]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Pad ids and return original lengths and labels in batch order."""
    ids, labels = zip(*batch, strict=True)
    lengths = torch.tensor([len(item) for item in ids], dtype=torch.long)
    padded = rnn.pad_sequence(ids, batch_first=True, padding_value=PAD_ID)
    return padded, lengths, torch.tensor(labels, dtype=torch.long)


class LSTMClassifier(nn.Module):
    """Classify a clause from the final hidden state of a packed LSTM."""

    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int, num_classes: int):
        """Create a trainable embedding, one LSTM layer, and a linear head."""
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_ID)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        """Return class logits for dynamically padded ids."""
        embedded = self.emb(ids)
        packed = rnn.pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, (hidden, _) = self.lstm(packed)
        return self.fc(hidden[-1])


def train_one_epoch(model, loader, optimizer, loss_fn, grad_clip: float = 1.0) -> float:
    """Train one epoch and return the mean batch loss."""
    model.train()
    device = next(model.parameters()).device
    losses = []
    for ids, lengths, labels in loader:
        optimizer.zero_grad()
        logits = model(ids.to(device), lengths)
        loss = loss_fn(logits, labels.to(device))
        loss.backward()
        clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        losses.append(float(loss.detach()))
    return float(np.mean(losses))


def predict(model, loader) -> np.ndarray:
    """Return softmax probabilities in loader order."""
    model.eval()
    device = next(model.parameters()).device
    probabilities = []
    with torch.no_grad():
        for ids, lengths, _ in loader:
            logits = model(ids.to(device), lengths)
            probabilities.append(torch.softmax(logits, dim=-1).cpu().numpy())
    return np.concatenate(probabilities).astype(np.float32)


def load_glove(words: list[str]) -> dict[str, np.ndarray]:
    """Load only requested 50-dimensional GloVe vectors from the cached archive."""
    archive = resolve_path(GLOVE_PATH)
    if not archive.exists():
        ensure_dir(archive.parent)
        urlretrieve(GLOVE_URL, archive)
    wanted = set(words)
    vectors = {}
    with gzip.open(archive, "rt", encoding="utf-8") as source:
        next(source)  # Word2Vec-style vocabulary size and dimension header.
        for line in source:
            word, _, values = line.partition(" ")
            if word in wanted:
                vectors[word] = np.array(values.split(), dtype=np.float32)
                if len(vectors) == len(wanted):
                    break
    return vectors


def _device(prefer: str | None) -> torch.device:
    """Select CUDA when available and requested, otherwise CPU, never MPS."""
    if prefer not in {None, "cpu", "cuda", "mps"}:
        raise ValueError(f"Unknown device: {prefer}")
    if prefer != "cpu" and prefer != "mps" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _loader(dataset: ClauseDataset, batch_size: int, shuffle: bool, seed: int) -> DataLoader:
    """Build a deterministic, single-process TP04 loader."""
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_fn,
                      generator=torch.Generator().manual_seed(seed), num_workers=0)


def _cross_entropy(probs: np.ndarray, labels: np.ndarray) -> float:
    """Compute mean cross-entropy from predicted probabilities."""
    return float(-np.log(np.clip(probs[np.arange(len(labels)), labels], 1e-12, 1)).mean())


def run_training(
    cfg: dict, data: dict[str, tuple[list[str], np.ndarray]], label_names: list[str], output_dir: str | Path,
) -> dict:
    """Train an LSTM, select the best validation epoch, and save a standard run."""
    from src.classification.train import plot_curves

    set_seed(cfg["seed"])
    device = _device(cfg.get("device"))
    print(f"Device: {device}", flush=True)
    train_texts = data["train"][0]
    counts = Counter(token for text in train_texts for token in tokenize(text))
    itos = build_vocab(counts, cfg["min_freq"])
    stoi = {word: index for index, word in enumerate(itos)}
    max_tokens = cfg["max_tokens"]
    truncated_share = sum(len(tokenize(text)) > max_tokens for text in train_texts) / len(train_texts)
    datasets = {split: ClauseDataset(texts, labels, stoi, max_tokens)
                for split, (texts, labels) in data.items()}
    loaders = {split: _loader(dataset, cfg["batch_size"] if split == "train" else cfg["eval_batch_size"],
                              split == "train", cfg["seed"])
               for split, dataset in datasets.items()}
    model = LSTMClassifier(len(itos), cfg["emb_dim"], cfg["hidden_dim"], len(label_names))
    glove_coverage = None
    if cfg["glove"]:
        if cfg["emb_dim"] != 50:
            raise ValueError("GloVe initialization requires emb_dim=50")
        vectors = load_glove(itos[2:])
        weights = np.random.default_rng(cfg["seed"]).normal(0, 0.1, size=(len(itos), 50)).astype(np.float32)
        weights[PAD_ID] = 0
        for word, vector in vectors.items():
            weights[stoi[word]] = vector
        with torch.no_grad():
            model.emb.weight.copy_(torch.from_numpy(weights))
        glove_coverage = len(vectors) / max(len(itos) - 2, 1)
        print(f"GloVe coverage: {len(vectors)}/{len(itos) - 2} ({glove_coverage:.1%})", flush=True)
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["lr"])
    loss_fn = nn.CrossEntropyLoss()
    best_score, best_epoch, best_state = -1.0, 0, None
    stale_epochs = 0
    history = []
    start = perf_counter()
    print(f"Vocabulary: {len(itos)}; steps per epoch: {len(loaders['train'])}", flush=True)
    for epoch in range(1, cfg["epochs"] + 1):
        epoch_start = perf_counter()
        train_loss = train_one_epoch(model, loaders["train"], optimizer, loss_fn, cfg["grad_clip"])
        val_probs = predict(model, loaders["validation"])
        val_labels = data["validation"][1]
        val_loss = _cross_entropy(val_probs, val_labels)
        val_metrics = evaluate(val_probs, val_labels, label_names)
        row = {"epoch": epoch, "train_loss": train_loss, "train_loss_blocks": [train_loss],
               "val_loss": val_loss, "val_accuracy": val_metrics["accuracy"],
               "val_macro_f1": val_metrics["macro_f1"], "lr_end": cfg["lr"],
               "epoch_time_s": perf_counter() - epoch_start}
        history.append(row)
        print(f"[{cfg['run_name']}] epoch {epoch}: train loss {train_loss:.3f}, val loss {val_loss:.3f}, "
              f"val macro-F1 {row['val_macro_f1']:.3f} ({row['epoch_time_s']:.0f}s)", flush=True)
        if row["val_macro_f1"] > best_score:
            best_score, best_epoch = row["val_macro_f1"], epoch
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= cfg["patience"]:
                break
    train_time_s = perf_counter() - start
    model.load_state_dict(best_state)
    val_probs = predict(model, loaders["validation"])
    test_probs = predict(model, loaders["test"])
    run_dir = ensure_dir(Path(output_dir) / cfg["run_name"])
    trainable_params = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    total_params = sum(parameter.numel() for parameter in model.parameters())
    run_config = {**cfg, "model_type": "lstm", "device": str(device), "n_train": len(train_texts),
                  "vocab_size": len(itos), "truncated_train_share": truncated_share,
                  "best_epoch": best_epoch, "trainable_params": trainable_params,
                  "total_params": total_params, "train_time_s": train_time_s}
    if glove_coverage is not None:
        run_config["glove_coverage"] = glove_coverage
    metrics = save_run(run_dir, run_config, val_probs, data["validation"][1],
                       test_probs, data["test"][1], label_names)
    save_json(history, run_dir / "history.json")
    plot_curves(history, run_dir / "training_curves.png", cfg["run_name"])
    model_dir = ensure_dir(run_dir / "model")
    torch.save(model.state_dict(), model_dir / "model.pt")
    save_json(itos, model_dir / "vocab.json")
    save_json({"vocab_size": len(itos), "emb_dim": cfg["emb_dim"], "hidden_dim": cfg["hidden_dim"],
               "num_classes": len(label_names), "max_tokens": max_tokens}, model_dir / "config.json")
    return metrics


class LSTMTextClassifier:
    """Reload a saved LSTM behind the common probability interface."""

    def __init__(self, model_dir: str | Path, device=None, batch_size: int = 256, max_tokens: int | None = None):
        """Load model weights, vocabulary, and token limit from a run model directory."""
        model_dir = resolve_path(model_dir)
        config = load_json(model_dir / "config.json")
        itos = load_json(model_dir / "vocab.json")
        self.stoi = {word: index for index, word in enumerate(itos)}
        self.max_tokens = max_tokens if max_tokens is not None else config["max_tokens"]
        self.batch_size = batch_size
        self.device = _device(device)
        self.model = LSTMClassifier(config["vocab_size"], config["emb_dim"], config["hidden_dim"],
                                    config["num_classes"]).to(self.device)
        state = torch.load(model_dir / "model.pt", map_location=self.device, weights_only=True)
        self.model.load_state_dict(state)
        self.model.eval()

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Return ordered float32 probabilities, including an empty batch case."""
        if not texts:
            return np.empty((0, self.model.fc.out_features), dtype=np.float32)
        dataset = ClauseDataset(texts, np.zeros(len(texts), dtype=np.int64), self.stoi, self.max_tokens)
        loader = _loader(dataset, self.batch_size, False, 42)
        return predict(self.model, loader)
