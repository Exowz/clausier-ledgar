"""Tests for checklist review and simulated contracts."""

import numpy as np

from src.review.checklist import (
    checklist_from_train,
    evaluate_simulation,
    review,
    review_contract,
    simulate_contracts,
    split_clauses,
)


def test_checklist_uses_training_frequency() -> None:
    assert checklist_from_train(np.array([2, 1, 2, 0, 1, 2]), ["a", "b", "c"], 2) == ["c", "b"]


def test_split_clauses_drops_short_heading() -> None:
    text = "Services Agreement\n\n" + "A" * 40 + "\n \n" + "B" * 45
    assert split_clauses(text) == ["A" * 40, "B" * 45]


def test_review_assigns_present_check_and_missing() -> None:
    probs = np.array([[0.9, 0.05, 0.05, 0], [0.1, 0.6, 0.3, 0]])
    result = review(probs, ["a", "b", "c", "d"], ["a", "b", "c"], 0.8)
    assert [row["status"] for row in result["checklist"]] == ["present", "check", "missing"]
    assert [row["clauses"] for row in result["checklist"]] == [[0], [1], []]
    assert [row["status"] for row in result["clauses"]] == ["confident", "check"]


def test_simulate_contracts_is_seeded_and_keeps_other_types_out() -> None:
    labels = np.repeat(np.arange(4), 30)
    first = simulate_contracts(labels, [0, 1], n_contracts=500, n_other=3)
    assert first == simulate_contracts(labels, [0, 1], n_contracts=500, n_other=3)
    assert 0.65 < sum(0 in row["present_types"] for row in first) / 500 < 0.75
    assert all(set(labels[row["indices"][-3:]]).isdisjoint({0, 1}) for row in first)


def test_evaluate_perfect_probabilities() -> None:
    labels = np.repeat(np.arange(4), 10)
    probs = np.eye(4)[labels]
    contracts = simulate_contracts(labels, [0, 1], n_contracts=30, n_other=2)
    result = evaluate_simulation(contracts, probs, labels, ["a", "b", "c", "d"], ["a", "b"], 0.8)
    assert result["missing_precision"] == 1.0
    assert result["missing_recall"] == 1.0
    assert result["check_share"] == 0.0
    assert result["truly_present"]["present"] == 1.0


def test_review_contract_scales_probabilities_and_includes_text() -> None:
    class Classifier:
        def predict_proba(self, texts: list[str]) -> np.ndarray:
            return np.array([[0.8, 0.2] for _ in texts])

    text = "A" * 45
    result = review_contract(text, Classifier(), ["a", "b"], ["a"], 0.7, temperature=2)
    assert result["clauses"][0]["text"] == text
    assert result["clauses"][0]["status"] == "check"
