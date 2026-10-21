"""Run the per-class, confusion, and text-slice audit for a saved run."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.audit.per_class import confused_examples, per_class_table, plot_f1_vs_count
from src.audit.slices import plot_slices, slice_metrics
from src.classification.run_io import load_run
from src.data import count_tokens, load_split, slice_frame
from src.utils import ensure_dir, resolve_path


def _markdown_table(table: pd.DataFrame, columns: list[str]) -> str:
    """Format selected dataframe columns as a plain Markdown table."""
    rows = ["| " + " | ".join(columns) + " |", "|" + "|".join(["---"] * len(columns)) + "|"]
    for _, row in table.iterrows():
        cells = [f"{row[column]:.3f}" if isinstance(row[column], (float, np.floating))
                 else str(row[column]).replace("|", "\\|").replace("\n", " ") for column in columns]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _slice_markdown(table: pd.DataFrame, heading: str) -> str:
    display = table.copy()
    display["accuracy (95% interval)"] = display.apply(
        lambda row: f"{row['accuracy']:.3f} [{row['acc_low']:.3f}, {row['acc_high']:.3f}]", axis=1)
    display["macro-F1 (95% interval)"] = display.apply(
        lambda row: f"{row['macro_f1']:.3f} [{row['f1_low']:.3f}, {row['f1_high']:.3f}]", axis=1)
    return (f"## {heading}\n\n" + _markdown_table(display,
            ["slice_type", "slice", "n", "n_classes", "accuracy (95% interval)",
             "macro-F1 (95% interval)", "reading"]) + "\n\n"
            "Reading uses accuracy: macro-F1 is computed over the clause types present in each slice, "
            "so it is not comparable between slices.\n")


def main(argv=None) -> None:
    """Audit one saved classifier run on full and deduplicated LEDGAR test sets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--out", default="reports/audit")
    parser.add_argument("--figures", default="reports/figures")
    args = parser.parse_args(argv)

    run_dir = resolve_path(args.run)
    name = run_dir.name
    run = load_run(run_dir)
    texts, test_labels = load_split("test")
    _, train_labels = load_split("train")
    if not np.array_equal(run["test_labels"], test_labels):
        raise ValueError("Run test labels do not match the cached LEDGAR test split")
    predictions = run["test_probs"].argmax(axis=1)
    token_path = resolve_path("outputs/data/test_n_tokens.npy")
    if token_path.exists():
        n_tokens = np.load(token_path)
        if len(n_tokens) != len(texts):
            raise ValueError("Cached token counts do not match the test split")
    else:
        n_tokens = count_tokens(texts, "nlpaueb/legal-bert-base-uncased")
        ensure_dir(token_path.parent)
        np.save(token_path, n_tokens)
    frame = slice_frame(texts, n_tokens, 256)
    mask = np.load(resolve_path("outputs/data/test_dedup_mask.npy"))
    if mask.shape != test_labels.shape or mask.dtype != np.bool_ or not mask.any():
        raise ValueError("Deduplication mask must be a nonempty boolean vector matching test labels")

    out_dir = ensure_dir(Path(args.out) / name)
    figures = ensure_dir(args.figures)
    label_names = run["metrics"]["label_names"]
    class_table = per_class_table(run["metrics"], train_labels, label_names)
    class_table.to_csv(out_dir / "per_class.csv", index=False)
    plot_f1_vs_count(class_table, figures / f"{name}_f1_vs_count.png", f"{name}: test F1 vs training count")
    worst = class_table.head(10)
    (out_dir / "worst_classes.md").write_text(
        "# Ten worst test classes\n\n" + _markdown_table(worst,
            ["label", "name", "train_count", "support", "precision", "recall", "f1"]) + "\n",
        encoding="utf-8")

    pairs = confused_examples(texts, test_labels, predictions, label_names,
                              run["metrics"]["test"]["top_confused"][:10])
    confusion_lines = ["# Ten most confused class pairs", "",
                       "Examples are sampled from test errors. Assess model error versus overlapping label "
                       "definitions by reading them.", ""]
    for pair in pairs:
        confusion_lines += [f"## {pair['name_a']} / {pair['name_b']}", "",
                            f"{pair['name_a']} as {pair['name_b']}: {pair['a_as_b']}; "
                            f"{pair['name_b']} as {pair['name_a']}: {pair['b_as_a']}; total: {pair['total']}", ""]
        for direction, key in ((f"{pair['name_a']} as {pair['name_b']}", "a_as_b_examples"),
                               (f"{pair['name_b']} as {pair['name_a']}", "b_as_a_examples")):
            confusion_lines.append(f"### {direction}")
            confusion_lines.append("")
            for example in pair[key]:
                confusion_lines.append(f"- Test index {example['index']}: {example['text'].replace(chr(10), ' ')}")
            confusion_lines.append("")
    (out_dir / "confusions.md").write_text("\n".join(confusion_lines) + "\n", encoding="utf-8")

    full = slice_metrics(test_labels, predictions, frame, n_boot=args.n_boot)
    dedup = slice_metrics(test_labels[mask], predictions[mask], frame.loc[mask].reset_index(drop=True),
                          n_boot=args.n_boot)
    pd.concat([full.assign(test_set="test"), dedup.assign(test_set="test_dedup")],
              ignore_index=True).to_csv(out_dir / "slices.csv", index=False)
    (out_dir / "slices.md").write_text(
        "# Text slice metrics\n\n" + _slice_markdown(full, "Full test set") + "\n" +
        _slice_markdown(dedup, "Deduplicated test set"), encoding="utf-8")
    plot_slices(full, figures / f"{name}_slices.png", f"{name}: test performance by text slice")

    observed, low, high = full.iloc[0][["macro_f1", "f1_low", "f1_high"]]
    print(f"{name} test macro-F1: {observed:.3f} [{low:.3f}, {high:.3f}]")
    print("Worst 5 classes:")
    for _, row in worst.head(5).iterrows():
        print(f"  {row['name']}: F1 {row['f1']:.3f}, train {row['train_count']}")
    for heading, table in (("test", full), ("test_dedup", dedup)):
        worse = table.loc[table["reading"] == "worse"]
        print(f"{heading} slices read as worse: " +
              (", ".join(f"{row['slice_type']}={row['slice']}" for _, row in worse.iterrows()) or "none"))


if __name__ == "__main__":
    main()
