"""Per-class results and examples from confused label pairs."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def per_class_table(metrics: dict, train_labels: np.ndarray, label_names: list[str]) -> pd.DataFrame:
    """Return test class metrics with train counts, sorted from worst F1."""
    counts = np.bincount(np.asarray(train_labels, dtype=int), minlength=len(label_names))
    rows = []
    for item in metrics["test"]["per_class"]:
        label = int(item["label"])
        rows.append({"label": label, "name": label_names[label], "train_count": int(counts[label]),
                     "support": int(item["support"]), "precision": float(item["precision"]),
                     "recall": float(item["recall"]), "f1": float(item["f1"])})
    return pd.DataFrame(rows).sort_values(["f1", "label"]).reset_index(drop=True)


def plot_f1_vs_count(table: pd.DataFrame, path: Path, title: str) -> None:
    """Plot test F1 against log-scale train count and annotate ten worst classes."""
    counts = table["train_count"].clip(lower=1)
    rank_count = table["train_count"].rank().to_numpy()
    rank_f1 = table["f1"].rank().to_numpy()
    correlation = float(np.corrcoef(rank_count, rank_f1)[0, 1]) if (np.std(rank_count) > 0 and
                                                                    np.std(rank_f1) > 0) else float("nan")
    plt.rcParams.update({"font.size": 12})
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(counts, table["f1"], alpha=0.65)
    for _, row in table.head(10).iterrows():
        ax.annotate(row["name"], (max(1, row["train_count"]), row["f1"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("Training examples per class (log scale)")
    ax.set_ylabel("Test F1")
    ax.set_title(f"{title}\nSpearman rank correlation: {correlation:.3f}")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def confused_examples(
    texts: list[str], y_true, pred, label_names, pairs: list[dict], k: int = 5,
    seed: int = 42, max_chars: int = 300,
) -> list[dict]:
    """Sample up to k mistaken clauses in each direction of each confused pair."""
    truth, predictions = np.asarray(y_true), np.asarray(pred)
    if len(texts) != len(truth) or predictions.shape != truth.shape:
        raise ValueError("Texts, labels, and predictions must be aligned")
    rng = np.random.default_rng(seed)
    results = []
    for pair in pairs[:10]:
        a, b = int(pair["a"]), int(pair["b"])
        result = {**pair, "name_a": label_names[a], "name_b": label_names[b]}
        for source, target, key in ((a, b, "a_as_b_examples"), (b, a, "b_as_a_examples")):
            indices = np.flatnonzero((truth == source) & (predictions == target))
            chosen = rng.choice(indices, size=min(k, len(indices)), replace=False)
            result[key] = [{"index": int(index), "text": texts[index][:max_chars]}
                           for index in chosen]
        results.append(result)
    return results
