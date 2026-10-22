"""Synthetic checks for paired run comparisons."""

import numpy as np
import pytest
from sklearn.metrics import f1_score

from src.classification import compare
from src.classification.run_io import save_run


def test_contingency_course_example() -> None:
    assert compare.contingency([0, 1, 2, 3, 0], [0, 1, 0, 0, 0], [0, 2, 2, 0, 1]) == (1, 2, 1, 1)


def test_mcnemar_course_examples() -> None:
    assert compare.mcnemar(0, 0) == (0.0, 1.0)
    assert compare.mcnemar(60, 40)[0] == pytest.approx(3.61)
    assert compare.mcnemar(60, 40)[1] == pytest.approx(0.0574, abs=1e-4)
    assert compare.mcnemar(25, 5)[0] == pytest.approx(361 / 30)


def test_paired_bootstrap_same_and_better_model() -> None:
    labels = np.tile(np.arange(4), 500)
    good = labels.copy()
    bad = labels.copy()
    bad[:1000] = (bad[:1000] + 1) % 4
    assert compare.paired_bootstrap(labels, good, good, n_boot=100) == (0.0, 0.0, 0.0)
    observed, low, high = compare.paired_bootstrap(labels, good, bad, n_boot=100)
    assert observed > 0
    assert 0 < low <= high


def test_paired_bootstrap_uses_each_resamples_true_classes_for_both_models() -> None:
    truth = np.array([0] * 20 + list(range(1, 9)))
    good = truth.copy()
    bad = np.zeros_like(truth)
    observed, low, high = compare.paired_bootstrap(truth, good, bad, n_boot=100)
    rng = np.random.default_rng(42)
    differences = []
    for _ in range(100):
        indices = rng.integers(0, len(truth), size=len(truth))
        labels = np.unique(truth[indices])
        differences.append(
            f1_score(truth[indices], good[indices], average="macro", labels=labels,
                     zero_division=0)
            - f1_score(truth[indices], bad[indices], average="macro", labels=labels,
                       zero_division=0)
        )
    assert observed > 0
    assert (low, high) == pytest.approx(np.percentile(differences, [2.5, 97.5]))


def test_compare_runs_uses_same_test_rows_and_dedup_mask(tmp_path) -> None:
    mask_path = tmp_path / "mask.npy"
    np.save(mask_path, np.array([True, False, True, True]))
    labels = np.array([0, 1, 0, 1])
    probs_a = np.array([[0.9, 0.1], [0.1, 0.9], [0.9, 0.1], [0.1, 0.9]])
    probs_b = np.array([[0.9, 0.1], [0.9, 0.1], [0.9, 0.1], [0.9, 0.1]])
    for name, probs in (("a", probs_a), ("b", probs_b)):
        save_run(tmp_path / name, {"run_name": name}, probs, labels, probs, labels,
                 ["zero", "one"], dedup_mask_path=mask_path)

    result = compare.compare_runs(tmp_path / "a", tmp_path / "b", n_boot=30, dedup_mask_path=mask_path)

    assert result["test"]["n"] == 4
    assert result["test_dedup"]["n"] == 3
    assert result["test"]["b"] == 2
    assert result["test"]["c"] == 0
    assert result["test"]["accuracy_a"] == 1.0
