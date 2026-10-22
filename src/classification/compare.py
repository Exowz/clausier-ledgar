"""Paired tests for two saved classifier runs."""

import argparse
import math
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score

from src.audit.stats import macro_f1
from src.classification.run_io import load_run
from src.utils import ensure_dir, resolve_path, save_json


def contingency(y_true, pred_a, pred_b) -> tuple[int, int, int, int]:
    """Count both right, only A right, only B right, and both wrong."""
    truth, a, b = np.asarray(y_true), np.asarray(pred_a), np.asarray(pred_b)
    if truth.shape != a.shape or truth.shape != b.shape:
        raise ValueError("Labels and predictions must have matching shapes")
    right_a, right_b = a == truth, b == truth
    return (int(np.sum(right_a & right_b)), int(np.sum(right_a & ~right_b)),
            int(np.sum(~right_a & right_b)), int(np.sum(~right_a & ~right_b)))


def mcnemar(b: int, c: int) -> tuple[float, float]:
    """Return continuity-corrected McNemar chi-squared statistic and p-value."""
    if b < 0 or c < 0:
        raise ValueError("Discordant counts must be nonnegative")
    if b + c == 0:
        return 0.0, 1.0
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    return chi2, math.erfc(math.sqrt(chi2 / 2))


def paired_bootstrap(
    y_true, pred_a, pred_b, n_boot: int = 1000, seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap the macro-F1 difference using shared example indices."""
    truth, a, b = np.asarray(y_true), np.asarray(pred_a), np.asarray(pred_b)
    if truth.ndim != 1 or len(truth) == 0 or a.shape != truth.shape or b.shape != truth.shape:
        raise ValueError("Labels and predictions must be nonempty matching vectors")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    observed_labels = np.unique(truth)
    observed = macro_f1(truth, a, observed_labels) - macro_f1(truth, b, observed_labels)
    rng = np.random.default_rng(seed)
    samples = np.empty(n_boot)
    for index in range(n_boot):
        chosen = rng.integers(0, len(truth), size=len(truth))
        sample_labels = np.unique(truth[chosen])
        samples[index] = (macro_f1(truth[chosen], a[chosen], sample_labels)
                          - macro_f1(truth[chosen], b[chosen], sample_labels))
    low, high = np.percentile(samples, [2.5, 97.5])
    return float(observed), float(low), float(high)


def _compare_subset(truth: np.ndarray, a: np.ndarray, b: np.ndarray, n_boot: int, seed: int) -> dict:
    labels = np.unique(truth)
    both, only_a, only_b, neither = contingency(truth, a, b)
    chi2, p_value = mcnemar(only_a, only_b)
    diff, low, high = paired_bootstrap(truth, a, b, n_boot=n_boot, seed=seed)
    return {
        "n": int(len(truth)), "accuracy_a": float(accuracy_score(truth, a)),
        "accuracy_b": float(accuracy_score(truth, b)),
        "macro_f1_a": macro_f1(truth, a, labels), "macro_f1_b": macro_f1(truth, b, labels),
        "a": both, "b": only_a, "c": only_b, "d": neither,
        "chi2": chi2, "p_value": p_value, "diff_macro_f1": diff,
        "diff_low": low, "diff_high": high, "mcnemar_significant": p_value < 0.05,
        "bootstrap_significant": low > 0 or high < 0,
    }


def compare_runs(
    run_a: str | Path, run_b: str | Path, n_boot: int = 1000, seed: int = 42,
    dedup_mask_path: str | Path = "outputs/data/test_dedup_mask.npy",
) -> dict:
    """Compare full and deduplicated test rows from two saved runs."""
    first, second = load_run(run_a), load_run(run_b)
    truth = first["test_labels"]
    if not np.array_equal(truth, second["test_labels"]):
        raise ValueError("Runs have different test_labels")
    pred_a = first["test_probs"].argmax(axis=1)
    pred_b = second["test_probs"].argmax(axis=1)
    mask = np.load(resolve_path(dedup_mask_path))
    if mask.shape != truth.shape or mask.dtype != np.bool_ or not mask.any():
        raise ValueError("Deduplication mask must be a nonempty boolean vector matching test labels")
    return {
        "a": Path(run_a).name, "b": Path(run_b).name,
        "test": _compare_subset(truth, pred_a, pred_b, n_boot, seed),
        "test_dedup": _compare_subset(truth[mask], pred_a[mask], pred_b[mask], n_boot, seed),
    }


def main(argv=None) -> None:
    """Write paired test results for two run directories as JSON and Markdown."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a", required=True)
    parser.add_argument("--b", required=True)
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--out", default="reports/audit")
    args = parser.parse_args(argv)
    result = compare_runs(args.a, args.b, n_boot=args.n_boot)
    print(write_comparison(result, args.out), end="")


def write_comparison(result: dict, out_dir: str | Path) -> str:
    """Write compare_<a>_vs_<b>.json and .md to out_dir and return the Markdown table."""
    output = ensure_dir(out_dir) / f"compare_{result['a']}_vs_{result['b']}"
    save_json(result, output.with_suffix(".json"))
    lines = [f"# {result['a']} vs {result['b']}", "",
             "| Set | n | Accuracy A | Accuracy B | Macro-F1 A | Macro-F1 B | a | b | c | d | Chi2 | p | "
             "F1 difference | 95% interval | McNemar significant | Bootstrap significant |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
    for key in ("test", "test_dedup"):
        row = result[key]
        lines.append(f"| {key} | {row['n']} | {row['accuracy_a']:.3f} | {row['accuracy_b']:.3f} | "
                     f"{row['macro_f1_a']:.3f} | {row['macro_f1_b']:.3f} | "
                     f"{row['a']} | {row['b']} | {row['c']} | {row['d']} | "
                     f"{row['chi2']:.3f} | {row['p_value']:.3f} | {row['diff_macro_f1']:.3f} | "
                     f"[{row['diff_low']:.3f}, {row['diff_high']:.3f}] | "
                     f"{row['mcnemar_significant']} | {row['bootstrap_significant']} |")
    markdown = "\n".join(lines) + "\n"
    output.with_suffix(".md").write_text(markdown, encoding="utf-8")
    return markdown


if __name__ == "__main__":
    main()
