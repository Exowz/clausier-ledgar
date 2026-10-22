"""Measure the effect of merging overlapping labels in saved classifier runs."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

from src.audit.stats import bootstrap_ci
from src.classification.compare import contingency, mcnemar, paired_bootstrap
from src.classification.run_io import load_run
from src.utils import ensure_dir, resolve_path, save_json, set_seed

MERGED_PAIRS: list[tuple[str, str]] = [
    ("Applicable Laws", "Governing Laws"),
    ("No Waivers", "Waivers"),
    ("Defined Terms", "Definitions"),
    ("Tax Withholdings", "Withholdings"),
    ("Amendments", "Modifications"),
    ("Authority", "Authorizations"),
    ("Binding Effects", "Successors"),
    ("Entire Agreements", "Integration"),
    ("Representations", "Warranties"),
]
DEDUP_MASK_PATH = Path("outputs/data/test_dedup_mask.npy")


def group_map(label_names: list[str], pairs: list[tuple[str, str]]) -> tuple[np.ndarray, list[str]]:
    """Map labels to groups ordered by the smallest original label ID."""
    if len(set(label_names)) != len(label_names):
        raise ValueError("Label names must be unique")
    ids = {name: index for index, name in enumerate(label_names)}
    members: dict[int, tuple[int, str]] = {}
    used: set[int] = set()
    for first, second in pairs:
        if first not in ids or second not in ids:
            raise ValueError(f"Unknown label in pair: {first} / {second}")
        a, b = ids[first], ids[second]
        if a == b or a in used or b in used:
            raise ValueError(f"Merged pairs must be disjoint: {first} / {second}")
        used.update((a, b))
        members[min(a, b)] = (max(a, b), f"{first} / {second}")
    mapping = np.empty(len(label_names), dtype=np.int64)
    names = []
    for index, label in enumerate(label_names):
        if index in used and index not in members:
            continue
        group_id = len(names)
        if index in members:
            other, name = members[index]
            mapping[index] = mapping[other] = group_id
            names.append(name)
        else:
            mapping[index] = group_id
            names.append(label)
    return mapping, names


def merge_probs(probs: np.ndarray, mapping: np.ndarray, n_groups: int) -> np.ndarray:
    """Sum saved label probabilities into the corresponding groups."""
    values = np.asarray(probs)
    groups = np.asarray(mapping)
    if values.ndim != 2 or values.shape[1] != len(groups):
        raise ValueError("Probability columns must match the mapping")
    if n_groups <= 0 or np.any(groups < 0) or np.any(groups >= n_groups):
        raise ValueError("Mapping contains an invalid group ID")
    merged = np.zeros((len(values), n_groups), dtype=values.dtype)
    for label_id, group_id in enumerate(groups):
        merged[:, group_id] += values[:, label_id]
    return merged


def _label_names(run: dict) -> list[str]:
    names = run["metrics"].get("label_names")
    if names is None:
        from src.data import get_label_names

        names = get_label_names()
    return list(names)


def _subset_metrics(
    truth: np.ndarray, original: np.ndarray, merged: np.ndarray, mapped_original: np.ndarray,
    mapping: np.ndarray, n_groups: int, label_names: list[str], n_boot: int,
) -> dict:
    before_accuracy = bootstrap_ci(truth, original, metric="accuracy", n_boot=n_boot, seed=42)
    before_f1 = bootstrap_ci(truth, original, metric="macro_f1", n_boot=n_boot, seed=42)
    merged_truth = mapping[truth]
    after_accuracy = bootstrap_ci(merged_truth, merged, metric="accuracy", n_boot=n_boot, seed=42)
    after_f1 = bootstrap_ci(merged_truth, merged, metric="macro_f1", n_boot=n_boot, seed=42)
    old_errors = original != truth
    recovered = old_errors & (merged == merged_truth)
    group_f1 = {}
    for group_id in range(n_groups):
        members = np.flatnonzero(mapping == group_id)
        if len(members) != 2:
            continue
        a, b = map(int, members)
        group_f1[f"{label_names[a]} / {label_names[b]}"] = {
            "f1_before_a": float(f1_score(truth, original, labels=[a], average="macro", zero_division=0)),
            "f1_before_b": float(f1_score(truth, original, labels=[b], average="macro", zero_division=0)),
            "f1_after": float(f1_score(merged_truth, merged, labels=[group_id], average="macro", zero_division=0)),
        }
    return {
        "n": int(len(truth)),
        "accuracy_before": before_accuracy,
        "accuracy_after": after_accuracy,
        "macro_f1_before": before_f1,
        "macro_f1_after": after_f1,
        "errors_before": int(old_errors.sum()),
        "errors_removed": int(recovered.sum()),
        "share_errors_removed": float(recovered.sum() / old_errors.sum()) if old_errors.any() else 0.0,
        "predictions_changed_by_sum": int(np.count_nonzero(merged != mapped_original)),
        "share_predictions_changed_by_sum": float(np.mean(merged != mapped_original)),
        "group_f1": group_f1,
    }


def _evaluate_run(
    run_dir: Path, mapping: np.ndarray, n_groups: int, dedup_mask: np.ndarray, n_boot: int,
) -> dict:
    run = load_run(run_dir)
    names = _label_names(run)
    probs = run["test_probs"]
    truth = run["test_labels"]
    if len(names) != len(mapping) or probs.shape != (len(truth), len(mapping)):
        raise ValueError(f"Label dimensions differ from the group mapping: {run_dir}")
    if dedup_mask.shape != truth.shape or dedup_mask.dtype != np.bool_ or not dedup_mask.any():
        raise ValueError("Deduplication mask must be a nonempty boolean vector matching test labels")
    original = probs.argmax(axis=1)
    merged = merge_probs(probs, mapping, n_groups).argmax(axis=1)
    mapped_original = mapping[original]
    results = {"run": Path(run_dir).name}
    for key, mask in (("test", np.ones(len(truth), dtype=bool)), ("test_dedup", dedup_mask)):
        results[key] = _subset_metrics(
            truth[mask], original[mask], merged[mask], mapped_original[mask], mapping,
            n_groups, names, n_boot,
        )
    return results


def evaluate_merge(run_dir: Path, mapping: np.ndarray, n_groups: int, dedup_mask: np.ndarray) -> dict:
    """Evaluate original and grouped predictions on full and deduplicated test rows."""
    return _evaluate_run(run_dir, mapping, n_groups, dedup_mask, n_boot=1000)


def _paired_results(run_a: dict, run_b: dict, mapping: np.ndarray, n_groups: int,
                    dedup_mask: np.ndarray, n_boot: int) -> dict:
    truth = run_a["test_labels"]
    if not np.array_equal(truth, run_b["test_labels"]):
        raise ValueError("Runs have different test_labels")
    a = merge_probs(run_a["test_probs"], mapping, n_groups).argmax(axis=1)
    b = merge_probs(run_b["test_probs"], mapping, n_groups).argmax(axis=1)
    merged_truth = mapping[truth]
    result = {}
    for key, mask in (("test", np.ones(len(truth), dtype=bool)), ("test_dedup", dedup_mask)):
        y, pred_a, pred_b = merged_truth[mask], a[mask], b[mask]
        _, only_a, only_b, _ = contingency(y, pred_a, pred_b)
        chi2, p_value = mcnemar(only_a, only_b)
        difference, low, high = paired_bootstrap(y, pred_a, pred_b, n_boot=n_boot, seed=42)
        result[key] = {
            "accuracy_a": float(accuracy_score(y, pred_a)),
            "accuracy_b": float(accuracy_score(y, pred_b)),
            "b": only_a, "c": only_b, "chi2": chi2, "p_value": p_value,
            "diff_macro_f1": difference, "diff_low": low, "diff_high": high,
            "mcnemar_significant": p_value < 0.05,
            "bootstrap_significant": low > 0 or high < 0,
        }
    return result


def _interval(values: tuple[float, float, float]) -> str:
    return f"{values[0]:.3f} [{values[1]:.3f}, {values[2]:.3f}]"


def _markdown(results: list[dict], paired: dict | None, n_groups: int) -> str:
    lines = [
        "# Overlapping labels: effect of merging nine pairs", "",
        "A pair of labels is merged if it is among the 10 most confused pairs of both TF-IDF and the best "
        "Legal-BERT run (`reports/audit/tfidf/confusions.md`, "
        "`reports/audit/legal_bert_long/confusions.md`) and the examples listed there show the two labels "
        "on the same kind of clause. Nine pairs meet this rule:", "",
    ]
    lines.extend(f"- {a} / {b}" for a, b in MERGED_PAIRS)
    lines.extend(["", "Merged group probability is the sum of its label probabilities; predictions use the "
                  "largest summed probability.", ""])
    for key, title in (("test", "Full test set"), ("test_dedup", "Deduplicated test set")):
        lines.extend([
            f"## {title}", "",
            "| Run | Accuracy before (95% interval) | Accuracy after (95% interval) | "
            "Macro-F1 before (95% interval) | Macro-F1 after (95% interval) | "
            "Share of errors removed | Predictions changed by probability sum |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ])
        for result in results:
            row = result[key]
            lines.append(
                f"| {result['run']} | {_interval(row['accuracy_before'])} | "
                f"{_interval(row['accuracy_after'])} | {_interval(row['macro_f1_before'])} | "
                f"{_interval(row['macro_f1_after'])} | {row['share_errors_removed']:.3f} | "
                f"{row['share_predictions_changed_by_sum']:.3f} |"
            )
        lines.append("")
    if paired is not None:
        lines.extend([
            "## Paired tests after merging", "",
            f"A: {results[0]['run']}; B: {results[1]['run']}.", "",
            "| question | A | B | test set | accuracy A | accuracy B | b | c | McNemar p | "
            "macro-F1 difference (A minus B) with interval | significant (McNemar / bootstrap) |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ])
        for key, name in (("test", "full"), ("test_dedup", "deduplicated")):
            row = paired[key]
            lines.append(
                f"| merged labels | {results[0]['run']} | {results[1]['run']} | {name} | "
                f"{row['accuracy_a']:.3f} | {row['accuracy_b']:.3f} | {row['b']} | {row['c']} | "
                f"{row['p_value']:.3f} | {row['diff_macro_f1']:.3f} "
                f"[{row['diff_low']:.3f}, {row['diff_high']:.3f}] | "
                f"{row['mcnemar_significant']} / {row['bootstrap_significant']} |"
            )
        lines.append("")
    for key, title in (("test", "Full test set"), ("test_dedup", "Deduplicated test set")):
        lines.extend([f"## Merged group F1: {title}", ""])
        headings = ["Group"]
        for result in results:
            headings.extend([f"{result['run']} label A before", f"{result['run']} label B before",
                             f"{result['run']} group after"])
        lines.append("| " + " | ".join(headings) + " |")
        lines.append("|---|" + "---:|" * (len(headings) - 1))
        for first, second in MERGED_PAIRS:
            name = f"{first} / {second}"
            values = []
            for result in results:
                scores = result[key]["group_f1"][name]
                values.extend(f"{scores[field]:.3f}" for field in ("f1_before_a", "f1_before_b", "f1_after"))
            lines.append("| " + " | ".join([name, *values]) + " |")
        lines.append("")
    lines.append(f"Recommendation: use the {n_groups}-group taxonomy for evaluation and review these nine "
                 "consolidated clause types with legal reviewers before changing training labels.")
    lines.append("")
    lines.append("Merging is evaluated from the saved probabilities, without retraining; a model trained on the "
                 "merged labels could do better.")
    return "\n".join(lines) + "\n"


DISPLAY_NAMES = {"tfidf": "TF-IDF + logistic regression", "legal_bert": "Legal-BERT (4 epochs)",
                 "legal_bert_long": "Legal-BERT (up to 10 epochs)"}


def _figure(results: list[dict], figures: Path) -> None:
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(10, 1.6 + 1.4 * len(results)))
    for index, result in enumerate(results):
        row = result["test"]
        for offset, key, label in ((0.15, "macro_f1_before", "100 labels"), (-0.15, "macro_f1_after", "91 groups")):
            values = row[key]
            ax.errorbar(values[0], index + offset, xerr=[[values[0] - values[1]], [values[2] - values[0]]],
                        fmt="o", markersize=9, capsize=4, color=f"C{index}",
                        markerfacecolor="white" if key == "macro_f1_before" else f"C{index}")
            ax.annotate(f"{label}: {values[0]:.3f}", (values[2], index + offset), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=11)
    ax.set_yticks(range(len(results)), [DISPLAY_NAMES.get(row["run"], row["run"]) for row in results])
    ax.set_ylim(-0.6, len(results) - 0.4)
    low = min(row["test"]["macro_f1_before"][1] for row in results)
    high = max(row["test"]["macro_f1_after"][2] for row in results)
    ax.set_xlim(low - 0.005, high + 0.03)
    ax.set_xlabel("Test macro-F1 (95% bootstrap interval)")
    ax.set_title("Macro-F1 before and after merging nine overlapping label pairs")
    fig.tight_layout()
    fig.savefig(ensure_dir(figures) / "taxonomy_merge.png", dpi=150)
    plt.close(fig)


def main(argv=None) -> None:
    """Evaluate saved runs and write taxonomy Markdown, JSON, and a full-test figure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("reports/audit"))
    parser.add_argument("--figures", type=Path, default=Path("reports/figures"))
    parser.add_argument("--n-boot", type=int, default=1000)
    args = parser.parse_args(argv)
    if args.n_boot <= 0:
        parser.error("--n-boot must be positive")
    set_seed(42)
    runs = [load_run(path) for path in args.runs]
    label_names = _label_names(runs[0])
    mapping, group_names = group_map(label_names, MERGED_PAIRS)
    truth = runs[0]["test_labels"]
    mask = np.load(resolve_path(DEDUP_MASK_PATH))
    if mask.shape != truth.shape or mask.dtype != np.bool_ or not mask.any():
        raise ValueError("Deduplication mask must be a nonempty boolean vector matching test labels")
    for run in runs[1:]:
        if _label_names(run) != label_names:
            raise ValueError("Runs have different label names")
    results = [_evaluate_run(path, mapping, len(group_names), mask, args.n_boot) for path in args.runs]
    paired = (_paired_results(runs[0], runs[1], mapping, len(group_names), mask, args.n_boot)
              if len(runs) >= 2 else None)
    payload = {"n_labels": len(label_names), "n_groups": len(group_names), "group_names": group_names,
               "mapping": mapping, "merged_pairs": MERGED_PAIRS, "runs": results, "paired_tests": paired,
               "n_boot": args.n_boot, "seed": 42}
    output = ensure_dir(args.out)
    markdown = _markdown(results, paired, len(group_names))
    save_json(payload, output / "taxonomy.json")
    (output / "taxonomy.md").write_text(markdown, encoding="utf-8")
    _figure(results, args.figures)
    print(markdown, end="")


if __name__ == "__main__":
    main()
