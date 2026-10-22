"""Measure saved classifier size, prediction latency, and int8 quality."""

import argparse
import gc
import platform
import tempfile
import time
from datetime import datetime
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score

from src.classification.predict import TransformerClassifier, load_classifier
from src.data import load_split
from src.utils import ensure_dir, load_json, resolve_path, save_json, set_seed


def sample_test(n: int, seed: int = 42) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Select a seeded, sorted sample from the full test split."""
    texts, labels = load_split("test")
    if not 1 <= n <= len(texts):
        raise ValueError(f"n must be between 1 and {len(texts)}")
    indices = np.sort(np.random.default_rng(seed).choice(len(texts), n, replace=False))
    return [texts[index] for index in indices], labels[indices], indices


def time_predict(classifier, texts: list[str], repeats: int = 3, warmup: int = 32) -> dict:
    """Warm up once, then report median prediction time and derived rates."""
    if not texts or repeats < 1 or warmup < 1:
        raise ValueError("texts must be nonempty, and repeats and warmup must be positive")
    classifier.predict_proba(texts[:warmup])
    durations = []
    for _ in range(repeats):
        start = time.perf_counter()
        classifier.predict_proba(texts)
        durations.append(time.perf_counter() - start)
    seconds = median(durations)
    per_clause = seconds / len(texts)
    return {
        "n": len(texts), "repeats": repeats, "seconds": seconds,
        "clauses_per_second": len(texts) / seconds,
        "ms_per_clause": per_clause * 1000,
        "seconds_per_1000": per_clause * 1000,
    }


def quantize_int8(classifier: TransformerClassifier) -> TransformerClassifier:
    """Replace CPU Linear layers with PyTorch dynamically quantized qint8 layers."""
    if platform.machine().lower() in {"arm64", "aarch64"}:
        if "qnnpack" in torch.backends.quantized.supported_engines:
            torch.backends.quantized.engine = "qnnpack"
    classifier.model = torch.ao.quantization.quantize_dynamic(
        classifier.model.cpu().eval(), {torch.nn.Linear}, dtype=torch.qint8,
    )
    return classifier


def size_on_disk_mb(path: Path) -> float:
    """Sum file bytes under a file or directory and return mebibytes."""
    path = Path(path)
    if path.is_file():
        total = path.stat().st_size
    elif path.is_dir():
        total = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    else:
        raise FileNotFoundError(path)
    return total / 1024**2


def _check_int8() -> str | None:
    """Return a reason when this Torch build cannot run dynamic int8 Linear."""
    if not hasattr(getattr(torch, "ao", None), "quantization"):
        return "torch.ao.quantization is unavailable"
    if not hasattr(torch.ao.quantization, "quantize_dynamic"):
        return "torch.ao.quantization.quantize_dynamic is unavailable"
    try:
        probe = type("Probe", (), {})()
        probe.model = torch.nn.Sequential(torch.nn.Linear(2, 2))
        quantize_int8(probe)
        if not isinstance(probe.model[0], torch.ao.nn.quantized.dynamic.Linear):
            return "dynamic quantization did not replace Linear"
        probe.model(torch.ones(1, 2))
    except (AttributeError, NotImplementedError, RuntimeError, TypeError) as exc:
        return f"dynamic int8 Linear failed: {exc}"
    return None


def _state_dict_size_mb(model: torch.nn.Module) -> float:
    """Measure a serialized state dict without retaining the temporary file."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "int8_state_dict.pt"
        torch.save(model.state_dict(), path)
        return size_on_disk_mb(path)


def _quality(classifier: TransformerClassifier, run_dir: Path) -> dict:
    """Compare int8 predictions on all test clauses with saved fp32 results."""
    texts, labels = load_split("test")
    probs = classifier.predict_proba(texts)
    fp32_probs = np.load(run_dir / "test_probs.npy")
    mask = np.load(resolve_path("outputs/data/test_dedup_mask.npy"))
    if len(texts) != 10_000 or probs.shape != fp32_probs.shape:
        raise ValueError("Int8 and saved fp32 probabilities must cover the full 10,000-row test split")
    if mask.shape != labels.shape or mask.dtype != np.bool_ or not mask.any():
        raise ValueError("Deduplication mask must match the full test split")
    predictions = probs.argmax(axis=1)
    labels_in_model = range(probs.shape[1])
    output_dir = ensure_dir("outputs/legal_bert_long_int8")
    np.save(output_dir / "test_probs.npy", probs)
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, labels=labels_in_model,
                                   average="macro", zero_division=0)),
        "dedup_macro_f1": float(f1_score(labels[mask], predictions[mask], labels=labels_in_model,
                                         average="macro", zero_division=0)),
        "agreement_with_fp32": float(np.mean(predictions == fp32_probs.argmax(axis=1))),
    }


DISPLAY_NAMES = {"tfidf": "TF-IDF", "legal_bert_long fp32": "Legal-BERT", "legal_bert_long int8": "Legal-BERT int8"}
DEVICE_NAMES = {"cpu": "CPU", "mps": "laptop GPU"}


def _plot_latency(rows: list[dict], path: Path) -> None:
    """Write a log scale bar chart of prediction time per clause."""
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [f"{DISPLAY_NAMES.get(row['configuration'], row['configuration'])}, "
              f"{DEVICE_NAMES.get(row['device'], row['device'])}" for row in rows]
    values = [row["ms_per_clause"] for row in rows]
    bars = ax.barh(labels, values)
    ax.set_xscale("log")
    ax.set_xlim(right=max(values) * 1.6)
    ax.invert_yaxis()
    for bar, value in zip(bars, values, strict=True):
        ax.text(value * 1.04, bar.get_y() + bar.get_height() / 2,
                f"{value:.2g} ms", va="center")
    ax.set_title("Prediction time per clause (laptop)")
    ax.set_xlabel("Milliseconds per clause (log scale)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _markdown(report: dict) -> str:
    """Render the measured costs and optional quality results as Markdown."""
    lines = [
        "# Cost and latency", "",
        (f"Machine: {report['machine']} ({report['processor'] or 'unknown'}); "
         f"Torch threads: {report['torch_threads']}; date: {report['date']}"), "",
        "| Configuration | Device | Size on disk (MB) | Parameters | ms per clause | "
        "Seconds per 1,000 clauses | Clauses per second |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["configurations"]:
        lines.append(
            f"| {row['configuration']} | {row['device']} | {row['size_mb']:.1f} | "
            f"{row['parameters']} | {row['ms_per_clause']:.1f} | "
            f"{row['seconds_per_1000']:.1f} | {row['clauses_per_second']:.1f} |"
        )
    if report.get("int8_skip_reason"):
        lines.extend(["", f"Int8 skipped: {report['int8_skip_reason']}"])
    if report.get("quality"):
        fp32 = report["quality"]["fp32"]
        int8 = report["quality"]["int8"]
        lines.extend([
            "", "| Model | Test accuracy | Test macro-F1 | Deduplicated macro-F1 | "
            "Agreement with fp32 |",
            "| --- | ---: | ---: | ---: | ---: |",
            (f"| fp32 saved | {fp32['accuracy']:.3f} | {fp32['macro_f1']:.3f} | "
             f"{fp32['dedup_macro_f1']:.3f} | {fp32['agreement_with_fp32']:.3f} |"),
            (f"| int8 | {int8['accuracy']:.3f} | {int8['macro_f1']:.3f} | "
             f"{int8['dedup_macro_f1']:.3f} | {int8['agreement_with_fp32']:.3f} |"),
        ])
    return "\n".join(lines) + "\n"


def main(argv=None) -> None:
    """Measure classifier costs and write JSON, Markdown, and a latency figure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tfidf", default="outputs/tfidf")
    parser.add_argument("--transformer", default="outputs/legal_bert_long")
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", default="reports")
    parser.add_argument("--skip-int8-quality", action="store_true")
    parser.add_argument("--devices", nargs="+", choices=("cpu", "mps"), default=["cpu", "mps"])
    args = parser.parse_args(argv)

    set_seed(42)
    torch.set_num_threads(torch.get_num_threads())
    tfidf_dir = resolve_path(args.tfidf)
    transformer_dir = resolve_path(args.transformer)
    out_dir = ensure_dir(args.out)
    texts, _, _ = sample_test(args.n)
    config = load_json(transformer_dir / "config.json")
    report = {
        "date": datetime.now().astimezone().date().isoformat(),
        "machine": platform.machine(), "processor": platform.processor(),
        "torch_threads": torch.get_num_threads(), "n": args.n,
        "repeats": args.repeats, "configurations": [],
    }

    if "cpu" in args.devices:
        tfidf = load_classifier(tfidf_dir)
        count = int(tfidf.classifier.coef_.size + len(tfidf.vectorizer.vocabulary_))
        timing = time_predict(tfidf, texts, repeats=args.repeats)
        report["configurations"].append({
            "configuration": "tfidf", "device": "cpu",
            "size_mb": size_on_disk_mb(tfidf_dir / "model.joblib"),
            "parameters": count, **timing,
        })
        del tfidf

        classifier = load_classifier(transformer_dir)
        classifier.model.to("cpu")
        classifier.device = torch.device("cpu")
        timing = time_predict(classifier, texts, repeats=args.repeats)
        report["configurations"].append({
            "configuration": "legal_bert_long fp32", "device": "cpu",
            "size_mb": size_on_disk_mb(transformer_dir / "model"),
            "parameters": f"{config['trainable_params']:,} / {config['total_params']:,}",
            "trainable_params": config["trainable_params"], "total_params": config["total_params"],
            **timing,
        })
        del classifier
        gc.collect()

    if "mps" in args.devices:
        if not torch.backends.mps.is_available():
            print("Skipping legal_bert_long fp32 on MPS: MPS is unavailable.")
        else:
            classifier = load_classifier(transformer_dir)
            classifier.model.to("mps")
            classifier.device = torch.device("mps")
            timing = time_predict(classifier, texts, repeats=args.repeats)
            report["configurations"].append({
                "configuration": "legal_bert_long fp32", "device": "mps",
                "size_mb": size_on_disk_mb(transformer_dir / "model"),
                "parameters": f"{config['trainable_params']:,} / {config['total_params']:,}",
                "trainable_params": config["trainable_params"], "total_params": config["total_params"],
                **timing,
            })
            del classifier
            gc.collect()

    if "cpu" in args.devices:
        reason = _check_int8()
        if reason:
            print(f"Skipping legal_bert_long int8 on CPU: {reason}")
            report["int8_skip_reason"] = reason
        else:
            try:
                classifier = load_classifier(transformer_dir)
                classifier.model.to("cpu")
                classifier.device = torch.device("cpu")
                quantize_int8(classifier)
                timing = time_predict(classifier, texts, repeats=args.repeats)
                report["configurations"].append({
                    "configuration": "legal_bert_long int8", "device": "cpu",
                    "size_mb": _state_dict_size_mb(classifier.model),
                    "parameters": f"{config['trainable_params']:,} / {config['total_params']:,}",
                    "trainable_params": config["trainable_params"],
                    "total_params": config["total_params"], **timing,
                })
                if not args.skip_int8_quality:
                    metrics = load_json(transformer_dir / "metrics.json")
                    report["quality"] = {
                        "fp32": {
                            "accuracy": metrics["test"]["accuracy"],
                            "macro_f1": metrics["test"]["macro_f1"],
                            "dedup_macro_f1": metrics["test_dedup"]["macro_f1"],
                            "agreement_with_fp32": 1.0,
                        },
                        "int8": _quality(classifier, transformer_dir),
                    }
                del classifier
                gc.collect()
            except (AttributeError, NotImplementedError, RuntimeError, TypeError) as exc:
                reason = f"dynamic int8 inference failed: {exc}"
                print(f"Skipping legal_bert_long int8 on CPU: {reason}")
                report["int8_skip_reason"] = reason
                report["configurations"] = [row for row in report["configurations"]
                                            if row["configuration"] != "legal_bert_long int8"]

    save_json(report, out_dir / "cost.json")
    markdown = _markdown(report)
    (out_dir / "cost.md").write_text(markdown, encoding="utf-8")
    _plot_latency(report["configurations"], ensure_dir(out_dir / "figures") / "cost_latency.png")
    print(markdown, end="")


if __name__ == "__main__":
    main()
