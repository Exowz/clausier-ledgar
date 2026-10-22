"""Assess saved classifier probabilities with calibration, abstention, and conformal sets."""

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from src.classification.run_io import load_run
from src.utils import ensure_dir, resolve_path


def confidence_and_prediction(probs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the largest probability and its class index for each clause."""
    values = np.asarray(probs)
    return values.max(axis=1), values.argmax(axis=1)


def reliability(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> pd.DataFrame:
    """Return one row per equal-width bin, with NaN means for empty bins."""
    confidence, prediction = confidence_and_prediction(probs)
    truth = np.asarray(labels)
    bins = np.minimum((confidence * n_bins).astype(int), n_bins - 1)
    rows = []
    for index in range(n_bins):
        chosen = bins == index
        rows.append({
            "bin_low": index / n_bins,
            "bin_high": (index + 1) / n_bins,
            "n": int(chosen.sum()),
            "mean_confidence": float(confidence[chosen].mean()) if chosen.any() else float("nan"),
            "accuracy": float((prediction[chosen] == truth[chosen]).mean()) if chosen.any() else float("nan"),
        })
    return pd.DataFrame(rows)


def ece(probs: np.ndarray, labels: np.ndarray, n_bins: int = 15) -> float:
    """Compute expected calibration error from nonempty reliability bins."""
    table = reliability(probs, labels, n_bins)
    return float((table["n"] * (table["accuracy"] - table["mean_confidence"]).abs()).sum() / len(labels))


def nll(probs: np.ndarray, labels: np.ndarray) -> float:
    """Return mean negative log probability of the true class."""
    values = np.asarray(probs)
    truth = np.asarray(labels)
    return float(-np.log(np.clip(values[np.arange(len(truth)), truth], 1e-12, None)).mean())


def apply_temperature(probs: np.ndarray, temperature: float) -> np.ndarray:
    """Scale log probabilities by a positive temperature and apply softmax."""
    if temperature <= 0:
        raise ValueError("Temperature must be positive")
    logits = np.log(np.clip(np.asarray(probs, dtype=np.float64), 1e-12, None)) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits)
    return exp_logits / exp_logits.sum(axis=1, keepdims=True)


def fit_temperature(probs: np.ndarray, labels: np.ndarray) -> float:
    """Choose the grid temperature with lowest validation negative log likelihood."""
    grid = np.exp(np.linspace(np.log(0.05), np.log(20), 400))
    losses = [nll(apply_temperature(probs, temperature), labels) for temperature in grid]
    return float(grid[int(np.argmin(losses))])


def abstention_threshold(
    probs: np.ndarray, labels: np.ndarray, target_accuracy: float = 0.95,
) -> float:
    """Return the smallest observed confidence reaching target covered accuracy."""
    confidence, prediction = confidence_and_prediction(probs)
    truth = np.asarray(labels)
    if float((prediction == truth).mean()) >= target_accuracy:
        return 0.0
    for threshold in np.unique(confidence):
        chosen = confidence >= threshold
        if float((prediction[chosen] == truth[chosen]).mean()) >= target_accuracy:
            return float(threshold)
    return 1.0


def coverage_curve(probs: np.ndarray, labels: np.ndarray, n_points: int = 101) -> pd.DataFrame:
    """Return test coverage and covered accuracy on an evenly spaced threshold grid."""
    confidence, prediction = confidence_and_prediction(probs)
    truth = np.asarray(labels)
    rows = []
    for threshold in np.linspace(0, 1, n_points):
        chosen = confidence >= threshold
        rows.append({"threshold": float(threshold), "coverage": float(chosen.mean()),
                     "accuracy": float((prediction[chosen] == truth[chosen]).mean())
                     if chosen.any() else float("nan")})
    return pd.DataFrame(rows)


def conformal_threshold(probs: np.ndarray, labels: np.ndarray, alpha: float = 0.1) -> float:
    """Return the higher split conformal quantile of one minus true-class probability."""
    if not 0 < alpha < 1:
        raise ValueError("Alpha must lie strictly between zero and one")
    values = np.asarray(probs)
    truth = np.asarray(labels)
    scores = 1 - values[np.arange(len(truth)), truth]
    level = np.ceil((len(truth) + 1) * (1 - alpha)) / len(truth)
    if level > 1:
        return 1.0
    return float(np.quantile(scores, level, method="higher"))


def prediction_sets(probs: np.ndarray, q_hat: float) -> list[np.ndarray]:
    """Return class indices whose probabilities exceed the conformal cutoff."""
    return [np.flatnonzero(row >= 1 - q_hat) for row in np.asarray(probs)]


def _covered_metrics(probs: np.ndarray, labels: np.ndarray, threshold: float) -> dict:
    confidence, prediction = confidence_and_prediction(probs)
    truth = np.asarray(labels)
    chosen = confidence >= threshold
    coverage = float(chosen.mean())
    return {
        "threshold": float(threshold),
        "test_coverage": coverage,
        "test_accuracy": float((prediction[chosen] == truth[chosen]).mean()) if chosen.any() else None,
        "test_macro_f1": float(f1_score(truth[chosen], prediction[chosen], average="macro", zero_division=0))
        if chosen.any() else None,
        "share_sent_to_human": 1 - coverage,
    }


def _reliability_records(table: pd.DataFrame) -> list[dict]:
    records = table.to_dict(orient="records")
    for row in records:
        for key in ("mean_confidence", "accuracy"):
            if pd.isna(row[key]):
                row[key] = None
    return records


def calibrate_run(run_dir: Path, target_accuracy: float = 0.95, alpha: float = 0.1) -> dict:
    """Summarize validation calibration and test abstention and conformal coverage."""
    run = load_run(run_dir)
    val_probs, val_labels = run["val_probs"], run["val_labels"]
    test_probs, test_labels = run["test_probs"], run["test_labels"]
    temperature = fit_temperature(val_probs, val_labels)
    scaled_val = apply_temperature(val_probs, temperature)
    scaled_test = apply_temperature(test_probs, temperature)
    calibration = {}
    for split, before, after, labels in (
        ("validation", val_probs, scaled_val, val_labels),
        ("test", test_probs, scaled_test, test_labels),
    ):
        calibration[split] = {
            "before": {"ece": ece(before, labels), "nll": nll(before, labels)},
            "after": {"ece": ece(after, labels), "nll": nll(after, labels)},
            "reliability_before": _reliability_records(reliability(before, labels)),
            "reliability_after": _reliability_records(reliability(after, labels)),
        }
    threshold = abstention_threshold(scaled_val, val_labels, target_accuracy)
    abstention = _covered_metrics(scaled_test, test_labels, threshold)
    abstention["target_accuracy"] = float(target_accuracy)
    abstention["no_abstention"] = _covered_metrics(scaled_test, test_labels, 0)
    q_hat = conformal_threshold(scaled_val, val_labels, alpha)
    sets = prediction_sets(scaled_test, q_hat)
    sizes = np.array([len(members) for members in sets])
    hits = np.array([label in members for label, members in zip(test_labels, sets, strict=True)])
    groups = {"0": sizes == 0, "1": sizes == 1, "2": sizes == 2, "3": sizes == 3,
              "4 or more": sizes >= 4}
    names = run["metrics"]["label_names"]
    pair_counts = Counter(tuple(names[index] for index in members) for members in sets if len(members) == 2)
    top_pairs = [{"labels": list(pair), "count": count} for pair, count in pair_counts.most_common(10)]
    conformal = {
        "alpha": float(alpha), "target_coverage": 1 - float(alpha), "q_hat": q_hat,
        "test_coverage": float(hits.mean()), "mean_set_size": float(sizes.mean()),
        "set_size_distribution": {key: float(chosen.mean()) for key, chosen in groups.items()},
        "coverage_per_set_size": {key: float(hits[chosen].mean()) if chosen.any() else None
                                  for key, chosen in groups.items()},
        "top_10_pairs": top_pairs,
    }
    curve = coverage_curve(scaled_test, test_labels)
    curve_records = curve.to_dict(orient="records")
    for row in curve_records:
        if pd.isna(row["accuracy"]):
            row["accuracy"] = None
    return {"run": Path(run_dir).name, "temperature": temperature, "calibration": calibration,
            "abstention": abstention, "conformal": conformal, "coverage_curve": curve_records}


def plot_reliability(run_name: str, before: pd.DataFrame, after: pd.DataFrame, path: Path) -> None:
    """Plot accuracy by confidence bin before and after temperature scaling."""
    plt.rcParams.update({"font.size": 12})
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharex=True, sharey=True)
    for ax, table, label in zip(axes, (before, after), ("Before scaling", "After scaling"), strict=True):
        error = float((table["n"] * (table["accuracy"] - table["mean_confidence"]).abs()).sum()
                      / table["n"].sum())
        widths = table["bin_high"] - table["bin_low"]
        ax.bar(table["bin_low"], table["accuracy"], width=widths, align="edge", edgecolor="white")
        ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1.5)
        ax.set_title(f"{DISPLAY_NAMES.get(run_name, run_name)}: {label}\nECE = {error:.3f}")
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    fig.tight_layout()
    output = resolve_path(path)
    ensure_dir(output.parent)
    fig.savefig(output, dpi=150)
    plt.close(fig)


DISPLAY_NAMES = {"tfidf": "TF-IDF + logistic regression", "legal_bert": "Legal-BERT (4 epochs)",
                 "legal_bert_long": "Legal-BERT (up to 10 epochs)"}


def plot_coverage(
    curves: dict[str, pd.DataFrame], thresholds: dict[str, float], path: Path,
    target_accuracy: float = 0.95,
) -> None:
    """Plot test coverage against covered accuracy and mark validation thresholds."""
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, curve in curves.items():
        ax.plot(curve["coverage"], curve["accuracy"], label=DISPLAY_NAMES.get(name, name), linewidth=2)
        chosen = curve.attrs.get("chosen_point")
        if chosen is None:
            row = curve.iloc[(curve["threshold"] - thresholds[name]).abs().argmin()]
            chosen = (row["coverage"], row["accuracy"])
        if chosen[1] is not None and not pd.isna(chosen[1]):
            ax.scatter(*chosen, s=75, zorder=3)
    ax.axhline(target_accuracy, color="black", linestyle="--", label=f"Target accuracy {target_accuracy:.2f}")
    ax.set_xlabel("Coverage")
    ax.set_ylabel("Accuracy of covered clauses")
    ax.set_title("Test accuracy and coverage by confidence threshold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0.85, 1.0)
    ax.legend(loc="lower left")
    fig.tight_layout()
    output = resolve_path(path)
    ensure_dir(output.parent)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _markdown(result: dict) -> str:
    name = result["run"]
    calibration = result["calibration"]
    calibration_rows = []
    for split in ("validation", "test"):
        values = calibration[split]
        calibration_rows.append([split, *(_fmt(values[stage][metric]) for stage in ("before", "after")
                                          for metric in ("ece", "nll"))])
    abstention = result["abstention"]
    abstention_rows = []
    for label, values in (("chosen threshold", abstention), ("no abstention", abstention["no_abstention"])):
        abstention_rows.append([label, *(_fmt(values[key]) for key in (
            "threshold", "test_coverage", "test_accuracy", "test_macro_f1", "share_sent_to_human"))])
    conformal = result["conformal"]
    conformal_rows = [
        ["Target coverage", _fmt(conformal["target_coverage"])],
        ["Test coverage", _fmt(conformal["test_coverage"])],
        ["Mean set size", _fmt(conformal["mean_set_size"])],
    ]
    for size in ("0", "1", "2", "3", "4 or more"):
        conformal_rows.append([f"Share of sets of size {size}", _fmt(conformal["set_size_distribution"][size])])
        conformal_rows.append([f"Coverage for sets of size {size}",
                               _fmt(conformal["coverage_per_set_size"][size])])
    pairs = conformal["top_10_pairs"]
    pair_lines = [f"- {pair['labels'][0]} / {pair['labels'][1]}: {pair['count']}" for pair in pairs]
    if not pair_lines:
        pair_lines = ["- None"]
    return "\n\n".join([
        f"# Calibration and abstention: {name}",
        "## Calibration\n\n" + _table(
            ["Split", "ECE before", "NLL before", "ECE after", "NLL after"], calibration_rows),
        f"Temperature fitted on validation: T = {result['temperature']:.3f}",
        f"## Abstention at target accuracy {abstention['target_accuracy']:.2f} "
        "(threshold chosen on validation)\n\n" + _table(
            ["Policy", "Threshold", "Test coverage", "Test accuracy", "Test macro-F1", "Share to human"],
            abstention_rows),
        f"## Conformal sets (alpha {conformal['alpha']:.2f}, q_hat {conformal['q_hat']:.3f} "
        "from validation)\n\n" + _table(["Measure", "Value"], conformal_rows),
        "### Most frequent two-label sets\n\n" + "\n".join(pair_lines),
    ]) + "\n"


def main(argv=None) -> None:
    """Write calibration reports and figures for one or more saved classifier runs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", nargs="+", type=Path, required=True)
    parser.add_argument("--target-accuracy", type=float, default=0.95)
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--out", type=Path, default=Path("reports/audit"))
    parser.add_argument("--figures", type=Path, default=Path("reports/figures"))
    args = parser.parse_args(argv)
    figures = ensure_dir(args.figures)
    curves = {}
    thresholds = {}
    for run_dir in args.run:
        result = calibrate_run(run_dir, args.target_accuracy, args.alpha)
        name = result["run"]
        report_dir = ensure_dir(args.out / name)
        (report_dir / "calibration.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
        markdown = _markdown(result)
        (report_dir / "calibration.md").write_text(markdown, encoding="utf-8")
        print(markdown, end="")
        test = result["calibration"]["test"]
        plot_reliability(name, pd.DataFrame(test["reliability_before"]),
                         pd.DataFrame(test["reliability_after"]), figures / f"{name}_reliability.png")
        curve = pd.DataFrame(result["coverage_curve"])
        curve.attrs["chosen_point"] = (result["abstention"]["test_coverage"],
                                       result["abstention"]["test_accuracy"])
        curves[name] = curve
        thresholds[name] = result["abstention"]["threshold"]
        plot_coverage({name: curve}, {name: thresholds[name]}, figures / f"{name}_coverage.png",
                      args.target_accuracy)
    if len(curves) > 1:
        plot_coverage(curves, thresholds, figures / "coverage_comparison.png", args.target_accuracy)


if __name__ == "__main__":
    main()
