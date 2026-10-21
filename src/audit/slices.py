"""Bootstrap performance tables and figures for text-derived slices."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.audit.stats import bootstrap_ci


def slice_metrics(
    y_true, pred, frame: pd.DataFrame, n_boot: int = 1000, seed: int = 42,
    min_n: int = 100,
) -> pd.DataFrame:
    """Summarize text slices and compare accuracy intervals with the whole set."""
    truth, predictions = np.asarray(y_true), np.asarray(pred)
    if truth.ndim != 1 or predictions.shape != truth.shape or len(frame) != len(truth):
        raise ValueError("Labels, predictions, and slice frame must be aligned")

    def measure(slice_type: str, name: str, mask: np.ndarray) -> dict:
        y, p = truth[mask], predictions[mask]
        accuracy, acc_low, acc_high = bootstrap_ci(y, p, "accuracy", n_boot, seed)
        f1, f1_low, f1_high = bootstrap_ci(y, p, "macro_f1", n_boot, seed)
        return {"slice_type": slice_type, "slice": name, "n": int(len(y)),
                "accuracy": accuracy, "acc_low": acc_low, "acc_high": acc_high,
                "macro_f1": f1, "f1_low": f1_low, "f1_high": f1_high,
                "n_classes": int(len(np.unique(y)))}

    all_row = measure("all", "all", np.ones(len(truth), dtype=bool))
    rows = [all_row]
    for slice_type in frame.columns:
        for name in frame[slice_type].dropna().unique():
            rows.append(measure(slice_type, str(name), frame[slice_type].to_numpy() == name))
    for row in rows:
        if row["slice_type"] == "all":
            row["reading"] = "reference"
        elif row["n"] < min_n:
            row["reading"] = "not interpreted (n < min_n)"
        elif row["acc_high"] < all_row["acc_low"]:
            row["reading"] = "worse"
        elif row["acc_low"] > all_row["acc_high"]:
            row["reading"] = "better"
        else:
            row["reading"] = "no evidence of a difference"
    return pd.DataFrame(rows)


def plot_slices(table: pd.DataFrame, path: Path, title: str) -> None:
    """Plot accuracy and within-slice macro-F1 intervals in fixed slice order."""
    all_row = table.iloc[0]
    order = {
        ("family", name): index for index, name in enumerate(
            ("credit", "employment", "license", "lease", "m&a", "other"))
    }
    order.update({
        ("jurisdiction", name): index + 6 for index, name in enumerate(
            ("delaware", "new_york", "other_us", "non_us", "none"))
    })
    order.update({
        ("length_bin", name): index + 11 for index, name in enumerate(
            ("<64", "64-127", "128-255", ">=256 (truncated)"))
    })
    rows = table.iloc[1:].copy()
    rows["_order"] = [order.get((row["slice_type"], row["slice"]), len(order))
                      for _, row in rows.iterrows()]
    rows = rows.sort_values("_order", kind="stable").reset_index(drop=True)
    plt.rcParams.update({"font.size": 12})
    fig, axes = plt.subplots(1, 2, figsize=(15, max(6, 0.55 * len(rows) + 2)), sharey=True)
    axes[0].axvspan(all_row["acc_low"], all_row["acc_high"], color="steelblue", alpha=0.15,
                    label="Whole test set 95% interval")
    axes[0].axvline(all_row["accuracy"], color="steelblue", linestyle="--")
    labels = []
    for index, row in rows.iterrows():
        color = "grey" if row["reading"].startswith("not interpreted") else "black"
        for ax, metric, low, high in ((axes[0], "accuracy", "acc_low", "acc_high"),
                                      (axes[1], "macro_f1", "f1_low", "f1_high")):
            ax.hlines(index, row[low], row[high], color=color)
            ax.vlines([row[low], row[high]], index - 0.1, index + 0.1, color=color)
            ax.plot(row[metric], index, "o", color=color)
        labels.append(f"{row['slice_type']}: {row['slice']} (n={row['n']})")
    axes[0].set_yticks(range(len(rows)), labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Accuracy with 95% bootstrap interval")
    axes[0].set_ylabel("Text slice")
    axes[0].set_title("Accuracy compared with whole test set")
    axes[0].legend(loc="lower right")
    axes[1].set_xlabel("Macro-F1 with 95% bootstrap interval")
    axes[1].set_title("Macro-F1 within the slice (not comparable across slices)")
    fig.suptitle(title)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
