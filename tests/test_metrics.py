"""Tests for shared classification metrics."""

import numpy as np
import pytest
from scipy.special import softmax
from sklearn.metrics import accuracy_score, f1_score

from src.classification.metrics import confusion, evaluate, top_confused_pairs


def test_evaluate_matches_sklearn_toy_example() -> None:
    logits = np.array([[2, 0, 0], [0, 1, 0], [0, 3, 0], [0, 0, 1]])
    labels = np.array([0, 0, 1, 2])
    probs = softmax(logits, axis=1)

    result = evaluate(probs, labels, ["zero", "one", "two"])

    assert result["n"] == 4
    assert result["accuracy"] == accuracy_score(labels, probs.argmax(axis=1)) == 0.75
    assert result["macro_f1"] == pytest.approx(f1_score(labels, probs.argmax(axis=1), labels=range(3), average="macro"))
    assert result["macro_f1"] == pytest.approx(7 / 9)
    assert result["micro_f1"] == pytest.approx(0.75)
    assert result["cross_entropy"] == pytest.approx(-np.log(probs[np.arange(4), labels]).mean())
    assert result["per_class"][0]["support"] == 2


def test_evaluate_includes_absent_class_in_macro_f1() -> None:
    probs = np.array([[0.9, 0.1, 0], [0.1, 0.9, 0]])
    result = evaluate(probs, np.array([0, 1]), ["zero", "one", "absent"])

    assert result["macro_f1"] == pytest.approx(2 / 3)
    assert result["per_class"][2]["f1"] == 0
    assert result["per_class"][2]["support"] == 0
    assert confusion(probs, np.array([0, 1]), n_classes=3).shape == (3, 3)


def test_top_confused_pairs_counts_both_directions() -> None:
    cm = np.array([[5, 3, 1], [2, 4, 0], [0, 4, 6]])

    pairs = top_confused_pairs(cm, ["a", "b", "c"], k=2)

    assert pairs == [
        {"a": 0, "b": 1, "name_a": "a", "name_b": "b", "a_as_b": 3, "b_as_a": 2, "total": 5},
        {"a": 1, "b": 2, "name_a": "b", "name_b": "c", "a_as_b": 0, "b_as_a": 4, "total": 4},
    ]


def test_evaluate_mask_restricts_rows() -> None:
    probs = np.array([[0.9, 0.1], [0.9, 0.1], [0.1, 0.9]])
    labels = np.array([0, 1, 1])

    result = evaluate(probs, labels, ["zero", "one"], mask=np.array([True, False, True]))

    assert result["n"] == 2
    assert result["accuracy"] == 1.0
