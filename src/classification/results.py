"""Build final classifier tables, paired tests, and a comparison figure."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.audit.stats import bootstrap_ci
from src.classification import compare
from src.classification.run_io import load_run
from src.utils import ensure_dir, load_json, resolve_path, save_json, set_seed

RUNS: dict[str, str] = {
    "tfidf": "TF-IDF + logistic regression",
    "lstm": "LSTM",
    "lstm_glove": "LSTM + GloVe",
    "bert_base": "BERT-base",
    "legal_bert": "Legal-BERT (4 epochs)",
    "legal_bert_long": "Legal-BERT (up to 10 epochs)",
    "legal_bert_lora": "Legal-BERT LoRA",
}

RESULT_COLUMNS = ["model", "best_epoch", "val_macro_f1", "test_accuracy", "test_micro_f1",
                  "test_macro_f1", "test_dedup_accuracy", "test_dedup_macro_f1", "train_time_min"]
LORA_COLUMNS = ["model", "trainable_params", "total_params", "trainable_share",
                "train_memory_gb_estimate", "train_time_min", "time_per_epoch_min",
                "test_macro_f1", "test_dedup_macro_f1"]
REFERENCE_LEXGLUE = [
    {"model": "TF-IDF + SVM", "micro_f1": 87.0, "macro_f1": 81.4},
    {"model": "BERT", "micro_f1": 87.6, "macro_f1": 81.8},
    {"model": "Legal-BERT", "micro_f1": 88.2, "macro_f1": 83.0},
]


def present_runs(outputs_dir: Path = Path("outputs")) -> list[str]:
    """Return known runs with saved metrics in display order."""
    root = resolve_path(outputs_dir)
    return [name for name in RUNS if (root / name / "metrics.json").is_file()]


def best_legal_bert(outputs_dir: Path = Path("outputs")) -> str | None:
    """Select the available full fine-tuning run using validation macro-F1."""
    root = resolve_path(outputs_dir)
    candidates = [name for name in ("legal_bert", "legal_bert_long")
                  if (root / name / "metrics.json").is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda name: load_json(root / name / "metrics.json")["validation"]["macro_f1"])


def _dedup_metric(metrics: dict, key: str) -> float | str:
    return metrics.get("test_dedup", {}).get(key, "")


def results_table(runs: list[str], outputs_dir: Path) -> pd.DataFrame:
    """Summarize validation, full test, deduplicated test, and training time per run."""
    root = resolve_path(outputs_dir)
    rows = []
    for name in runs:
        config = load_json(root / name / "config.json")
        metrics = load_json(root / name / "metrics.json")
        rows.append({
            "model": RUNS[name],
            "best_epoch": "" if name == "tfidf" else config.get("best_epoch", ""),
            "val_macro_f1": metrics["validation"]["macro_f1"],
            "test_accuracy": metrics["test"]["accuracy"],
            "test_micro_f1": metrics["test"]["micro_f1"],
            "test_macro_f1": metrics["test"]["macro_f1"],
            "test_dedup_accuracy": _dedup_metric(metrics, "accuracy"),
            "test_dedup_macro_f1": _dedup_metric(metrics, "macro_f1"),
            "train_time_min": "" if name == "tfidf" else config.get("train_time_s", 0) / 60,
        })
    return pd.DataFrame(rows, columns=RESULT_COLUMNS)


def lora_table(runs: list[str], outputs_dir: Path) -> pd.DataFrame:
    """Summarize full fine-tuning and LoRA resource and test metrics."""
    root = resolve_path(outputs_dir)
    rows = []
    for name in runs:
        if name not in {"legal_bert", "legal_bert_long", "legal_bert_lora"}:
            continue
        config = load_json(root / name / "config.json")
        metrics = load_json(root / name / "metrics.json")
        epochs = len(load_json(root / name / "history.json"))
        train_time_min = config["train_time_s"] / 60
        rows.append({
            "model": RUNS[name],
            "trainable_params": config["trainable_params"],
            "total_params": config["total_params"],
            "trainable_share": 100 * config["trainable_params"] / config["total_params"],
            "train_memory_gb_estimate": config["train_memory_gb_estimate"],
            "train_time_min": train_time_min,
            "time_per_epoch_min": train_time_min / epochs,
            "test_macro_f1": metrics["test"]["macro_f1"],
            "test_dedup_macro_f1": _dedup_metric(metrics, "macro_f1"),
        })
    return pd.DataFrame(rows, columns=LORA_COLUMNS)


def pairs(outputs_dir: Path) -> list[tuple[str, str, str]]:
    """Return the prespecified comparisons for pairs of available runs."""
    available = set(present_runs(outputs_dir))
    best = best_legal_bert(outputs_dir)
    requested = [
        (best, "tfidf", "main comparison"),
        ("legal_bert", "bert_base", "legal pretraining, same 4-epoch budget"),
        ("legal_bert_lora", "legal_bert", "LoRA versus full fine-tuning, same budget"),
        ("lstm", "tfidf", "LSTM versus TF-IDF"),
        ("lstm_glove", "lstm", "GloVe initialisation"),
    ]
    return [(a, b, question) for a, b, question in requested if a in available and b in available]


def plot_models(
    runs: list[str], outputs_dir: Path, path: Path, n_boot: int = 1000, seed: int = 42,
) -> None:
    """Plot full and deduplicated test macro-F1 with bootstrap intervals."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = resolve_path(outputs_dir)
    mask_path = root / "data" / "test_dedup_mask.npy"
    mask = np.load(mask_path) if mask_path.is_file() else None
    fig, ax = plt.subplots(figsize=(10, max(6, 0.8 * len(runs) + 2)))
    bounds = [0.6, 0.9]
    for index, name in enumerate(runs):
        run = load_run(root / name)
        truth = run["test_labels"]
        prediction = run["test_probs"].argmax(axis=1)
        full = bootstrap_ci(truth, prediction, n_boot=n_boot, seed=seed)
        bounds.extend(full)
        ax.errorbar(full[0], index - 0.08,
                    xerr=[[full[0] - full[1]], [full[2] - full[0]]], fmt="o",
                    color="tab:blue", capsize=4, markersize=7,
                    label="Full test" if index == 0 else None)
        if mask is not None and mask.shape == truth.shape and mask.any():
            dedup = bootstrap_ci(truth[mask], prediction[mask], n_boot=n_boot, seed=seed)
            bounds.extend(dedup)
            ax.errorbar(dedup[0], index + 0.08,
                        xerr=[[dedup[0] - dedup[1]], [dedup[2] - dedup[0]]], fmt="o",
                        color="tab:orange", markerfacecolor="white", capsize=4, markersize=7,
                        label="Deduplicated test" if index == 0 else None)
    if "tfidf" in runs:
        baseline = load_json(root / "tfidf" / "metrics.json")["test"]["macro_f1"]
        ax.axvline(baseline, color="gray", linestyle="--", label="TF-IDF test macro-F1")
        bounds.append(baseline)
    ax.set_yticks(range(len(runs)), [RUNS[name] for name in runs])
    ax.set_ylim(-0.5, len(runs) - 0.5)
    ax.invert_yaxis()
    ax.set_xlim(min(bounds) - (0.01 if min(bounds) < 0.6 else 0),
                max(bounds) + (0.01 if max(bounds) > 0.9 else 0))
    ax.set_xlabel("Macro-F1", fontsize=12)
    ax.set_ylabel("Model", fontsize=12)
    ax.set_title("Test macro-F1 per model (95% bootstrap intervals)", fontsize=14)
    ax.tick_params(labelsize=12)
    ax.grid(axis="x", alpha=0.25)
    if runs:
        ax.legend(fontsize=12)
    fig.tight_layout()
    output = resolve_path(path)
    ensure_dir(output.parent)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _format_cell(column: str, value: object) -> str:
    if value == "" or value is None:
        return ""
    if column in {"trainable_params", "total_params"}:
        return f"{value:,}"
    if column == "best_epoch":
        return str(value)
    if isinstance(value, (float, np.floating)):
        return f"{value:.3f}"
    return str(value)


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_format_cell(column, value)
                                        for column, value in zip(columns, row, strict=True)) + " |")
    return "\n".join(lines)


def _p_value(value: float) -> str:
    return "< 0.0001" if value < 0.0001 else f"{value:.4f}"


def _paired_table(comparisons: list[dict]) -> str:
    columns = ["question", "A", "B", "test set", "accuracy A", "accuracy B", "b", "c",
               "McNemar p", "macro-F1 difference (A minus B) with interval",
               "significant (McNemar / bootstrap)"]
    lines = ["| " + " | ".join(columns) + " |",
             "| " + " | ".join("---" for _ in columns) + " |"]
    for result in comparisons:
        for key, label in (("test", "full"), ("test_dedup", "deduplicated")):
            row = result[key]
            diff = f"{row['diff_macro_f1']:.3f} [{row['diff_low']:.3f}, {row['diff_high']:.3f}]"
            significance = f"{row['mcnemar_significant']} / {row['bootstrap_significant']}"
            cells = [result["question"], RUNS[result["a"]], RUNS[result["b"]], label,
                     f"{row['accuracy_a']:.3f}", f"{row['accuracy_b']:.3f}", str(row["b"]),
                     str(row["c"]), _p_value(row["p_value"]), diff, significance]
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None) -> None:
    """Build final reports from saved runs, or print the selected Legal-BERT run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument("--out", type=Path, default=Path("reports"))
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--print-best", action="store_true")
    args = parser.parse_args(argv)
    best = best_legal_bert(args.outputs)
    if args.print_best:
        if best is not None:
            print(best)
        return

    set_seed(42)
    available = present_runs(args.outputs)
    for name in RUNS:
        if name not in available:
            print(f"skipped {name}: not found")
    results = results_table(available, args.outputs)
    lora = lora_table(available, args.outputs)
    output = ensure_dir(args.out)
    comparisons = []
    mask_path = resolve_path(args.outputs) / "data" / "test_dedup_mask.npy"
    for a, b, question in pairs(args.outputs):
        pair = compare.compare_runs(resolve_path(args.outputs) / a, resolve_path(args.outputs) / b,
                                    n_boot=args.n_boot, dedup_mask_path=mask_path)
        compare.write_comparison(pair, output / "audit")
        comparisons.append({"question": question, **pair})
    plot_models(available, args.outputs, output / "figures" / "model_comparison.png",
                n_boot=args.n_boot, seed=42)

    selected = RUNS[best] if best else "none available"
    reference_rows = "\n".join(
        f"| {row['model']} | {row['micro_f1']:.1f} | {row['macro_f1']:.1f} |"
        for row in REFERENCE_LEXGLUE
    )
    markdown = "\n\n".join([
        "# Results",
        "Generated by `make results` from `outputs/`; do not edit by hand.",
        "## Results table\n\n" + _markdown_table(results) +
        f"\n\nBest Legal-BERT run, chosen on validation macro-F1: {selected}.",
        "## LoRA trade-off\n\n" + _markdown_table(lora) +
        "\n\nMemory: weights, gradients and Adam states only (activations excluded), "
        "from `training_memory_gb` in `src/classification/lora.py`.",
        "## Paired tests\n\n" + _paired_table(comparisons),
        "## Reference: LexGLUE (published)\n\n"
        "Published LEDGAR test numbers, not produced by this repository.\n\n"
        "| Model | Micro-F1 | Macro-F1 |\n"
        "| --- | --- | --- |\n" + reference_rows + "\n\n"
        "Chalkidis et al. 2022, LexGLUE (ACL), github.com/coastalcph/lex-glue.\n\n"
        "Their models read up to 512 tokens and train up to 20 epochs with batch size 8; ours read 256 tokens.",
    ]) + "\n"
    (output / "results.md").write_text(markdown, encoding="utf-8")
    save_json({"best_legal_bert": best, "results_table": results.to_dict(orient="records"),
               "lora_table": lora.to_dict(orient="records"), "pairs": comparisons,
               "reference_lexglue": REFERENCE_LEXGLUE}, output / "results.json")
    print(markdown, end="")


if __name__ == "__main__":
    main()
