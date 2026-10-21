"""Synthetic checks for per-class and slice audit summaries."""

import numpy as np
import pandas as pd

from src.audit.per_class import confused_examples, per_class_table
from src.audit.slices import plot_slices, slice_metrics
from src.audit.stats import bootstrap_ci


def test_bootstrap_interval_and_constant_metric() -> None:
    truth = np.tile([0, 1], 50)
    pred = truth.copy()
    pred[:20] = 1 - pred[:20]
    observed, low, high = bootstrap_ci(truth, pred, n_boot=200)
    assert low <= observed <= high
    assert bootstrap_ci(truth, truth, metric="accuracy", n_boot=30) == (1.0, 1.0, 1.0)


def test_bootstrap_rare_classes_keeps_observed_inside_interval() -> None:
    truth = np.array([0] * 100 + list(range(1, 11)))
    observed, low, high = bootstrap_ci(truth, truth, n_boot=200)
    assert low <= observed <= high
    assert (observed, low, high) == (1.0, 1.0, 1.0)


def test_slice_label_set_is_true_labels_in_slice() -> None:
    truth = np.array([0, 1, 2, 2])
    frame = pd.DataFrame({"family": ["two", "two", "other", "other"]})
    table = slice_metrics(truth, truth, frame, n_boot=10, min_n=1)
    two = table.loc[table["slice"] == "two"].iloc[0]
    assert two["n_classes"] == 2
    assert two["macro_f1"] == 1.0


def test_slice_reading_rule() -> None:
    truth = np.tile([0, 1], 150)
    pred = truth.copy()
    pred[200:] = 1 - pred[200:]
    frame = pd.DataFrame({"family": ["good"] * 195 + ["small"] * 5 + ["bad"] * 100})
    table = slice_metrics(truth, pred, frame, n_boot=100, min_n=20)
    readings = dict(zip(table["slice"], table["reading"], strict=True))
    assert readings["small"] == "not interpreted (n < min_n)"
    assert readings["bad"] == "worse"


def test_slice_reading_uses_accuracy_when_macro_f1_disagrees() -> None:
    truth = np.array([0] * 190 + [1] * 10 + [0, 1] * 100)
    pred = truth.copy()
    pred[190:200] = 0
    pred[200:250] = 1 - pred[200:250]
    frame = pd.DataFrame({"family": ["rare"] * 200 + ["balanced"] * 200})
    table = slice_metrics(truth, pred, frame, n_boot=200)
    all_row = table.iloc[0]
    rare = table.loc[table["slice"] == "rare"].iloc[0]
    assert rare["f1_high"] < all_row["f1_low"]
    assert rare["acc_low"] > all_row["acc_high"]
    assert rare["reading"] == "better"


def test_confused_examples_limits_each_direction() -> None:
    truth = np.array([0] * 8 + [1] * 8)
    pred = np.array([1] * 8 + [0] * 8)
    pairs = [{"a": 0, "b": 1, "a_as_b": 8, "b_as_a": 8, "total": 16}]
    result = confused_examples(["long clause text"] * 16, truth, pred, ["zero", "one"], pairs,
                               k=3, max_chars=4)
    assert len(result) == 1
    assert len(result[0]["a_as_b_examples"]) == 3
    assert len(result[0]["b_as_a_examples"]) == 3
    assert all(len(item["text"]) <= 4 for item in result[0]["a_as_b_examples"])


def test_per_class_table_sorted_and_train_counts() -> None:
    metrics = {"test": {"per_class": [
        {"label": 0, "name": "zero", "support": 5, "precision": 1, "recall": 1, "f1": 1},
        {"label": 1, "name": "one", "support": 2, "precision": 0.2, "recall": 0.3, "f1": 0.24},
    ]}}
    table = per_class_table(metrics, np.array([0, 0, 1]), ["zero", "one"])
    assert table["label"].tolist() == [1, 0]
    assert table["train_count"].tolist() == [1, 2]


def test_plot_slices_accepts_percentile_interval_excluding_observed(tmp_path) -> None:
    table = pd.DataFrame([
        {"slice_type": "all", "slice": "all", "n": 200, "accuracy": 0.8,
         "acc_low": 0.78, "acc_high": 0.82, "macro_f1": 0.5,
         "f1_low": 0.48, "f1_high": 0.52, "reading": "reference"},
        {"slice_type": "family", "slice": "rare", "n": 3, "accuracy": 0.7,
         "acc_low": 0.6, "acc_high": 0.8, "macro_f1": 0.9,
         "f1_low": 0.3, "f1_high": 0.8, "reading": "not interpreted (n < min_n)"},
    ])
    path = tmp_path / "slices.png"
    plot_slices(table, path, "test")
    assert path.exists()
