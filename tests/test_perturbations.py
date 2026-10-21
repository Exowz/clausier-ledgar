"""Synthetic checks for counterfactual edits and their controls."""

import runpy

import joblib
import numpy as np
import pytest

from src.audit import perturbations
from src.classification import baseline
from src.classification.baseline import TfidfClassifier


def test_roles_swap_once_and_preserve_case_and_plural() -> None:
    assert perturbations.swap_roles("The Buyer shall pay the Seller.") == "The Seller shall pay the Buyer."
    assert perturbations.swap_roles("LENDERS and borrowers") == "BORROWERS and lenders"
    assert perturbations.swap_roles("No named party appears.") is None
    assert perturbations.rename_roles("The Buyer shall pay the Seller.") == (
        "The Purchaser shall pay the Vendor."
    )
    assert perturbations.rename_roles("No named party appears.") is None


def test_jurisdiction_edit_and_control_share_matches() -> None:
    assert perturbations.jurisdiction_non_us("laws of the State of New York") == "laws of England and Wales"
    assert perturbations.jurisdiction_us("laws of the State of New York") == "laws of the State of Illinois"
    assert perturbations.jurisdiction_non_us("The State of Delaware") == "England and Wales"
    assert perturbations.jurisdiction_us("The State of Delaware") == "The State of Illinois"
    assert perturbations.jurisdiction_non_us("State of Delaware; Delaware corporation") == (
        "England and Wales; England and Wales corporation"
    )
    assert perturbations.jurisdiction_us("State of Delaware; Delaware corporation") == (
        "State of Illinois; Illinois corporation"
    )
    assert perturbations.jurisdiction_non_us("laws of California") is None
    assert perturbations.jurisdiction_us("laws of California") is None


@pytest.mark.parametrize(
    ("number", "words"),
    [(1, "one"), (21, "twenty-one"), (45, "forty-five"),
     (120, "one hundred twenty"), (365, "three hundred sixty-five")],
)
def test_number_to_words(number: int, words: str) -> None:
    assert perturbations.number_to_words(number) == words


def test_number_format_and_value_control() -> None:
    assert perturbations.number_format("thirty (30) days and 30 days") == (
        "30 days and thirty (30) days"
    )
    assert perturbations.number_value("thirty (30) days and 30 days") == (
        "forty-five (45) days and 45 days"
    )
    assert perturbations.number_format("ninety (90) Business Days") == "90 Business Days"
    assert perturbations.number_value("ninety (90) Business Days") == "one hundred five (105) Business Days"
    assert perturbations.number_format("indefinite duration") is None
    assert perturbations.number_value("indefinite duration") is None
    assert perturbations.number_format("unknown (30) days") is None
    assert perturbations.number_value("unknown (30) days") is None


def test_build_cases_samples_common_clauses_in_sorted_order() -> None:
    texts = ["Buyer pays Seller", "No party", "Lender pays", "Tenant leases", "Another clause"]
    cases = perturbations.build_cases(texts, "party_roles", max_n=2, seed=42)
    assert len(cases["idx"]) == len(cases["edited"]) == len(cases["control"]) == 2
    assert cases["idx"] == sorted(cases["idx"])
    for index, edited, control in zip(cases["idx"], cases["edited"], cases["control"], strict=True):
        assert edited == perturbations.swap_roles(texts[index])
        assert control == perturbations.rename_roles(texts[index])


def test_flip_stats_uses_paired_bootstrap_and_accuracy() -> None:
    original = np.zeros(10, dtype=int)
    edited = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    control = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    truth = np.zeros(10, dtype=int)
    stats = perturbations.flip_stats(original, edited, control, truth, n_boot=1000)
    assert stats["n"] == 10
    assert stats["flip_rate"] == pytest.approx(0.4)
    assert stats["ctrl_flip_rate"] == pytest.approx(0.2)
    assert stats["diff"] == pytest.approx(0.2)
    assert stats["acc_orig"] == 1.0
    assert stats["acc_edit"] == pytest.approx(0.6)
    assert stats["acc_ctrl"] == pytest.approx(0.8)
    for observed, low, high in (("flip_rate", "flip_low", "flip_high"),
                                ("ctrl_flip_rate", "ctrl_low", "ctrl_high"),
                                ("diff", "diff_low", "diff_high"),
                                ("acc_orig", "acc_orig_low", "acc_orig_high"),
                                ("acc_edit", "acc_edit_low", "acc_edit_high"),
                                ("acc_ctrl", "acc_ctrl_low", "acc_ctrl_high")):
        assert stats[low] <= stats[observed] <= stats[high]
    assert stats["diff_low"] >= 0


def test_decision_requires_both_conditions() -> None:
    assert perturbations.decide({"flip_rate": 0.03, "diff_low": 0.01}) == "fail"
    assert perturbations.decide({"flip_rate": 0.02, "diff_low": 0.01}) == "pass"
    assert perturbations.decide({"flip_rate": 0.03, "diff_low": 0.0}) == "pass"


def test_run_writes_results_and_repredicts_original(tmp_path, monkeypatch) -> None:
    class TinyClassifier:
        def __init__(self) -> None:
            self.inputs = []

        def predict_proba(self, texts: list[str]) -> np.ndarray:
            self.inputs.append(texts)
            return np.array([[0.1, 0.9] if "Seller" in text else [0.9, 0.1] for text in texts])

    classifier = TinyClassifier()
    monkeypatch.setattr(perturbations, "load_classifier", lambda _: classifier)
    monkeypatch.setattr(perturbations, "load_split", lambda _: (["Buyer pays |", "Unchanged"], np.array([0, 0])))
    monkeypatch.setattr(perturbations, "get_label_names", lambda: ["zero", "one"])
    result = perturbations.run_counterfactual(tmp_path / "tiny", max_n=5, n_boot=20, out_dir=tmp_path)
    assert result["party_roles"]["n"] == 1
    assert result["party_roles"]["flip_rate"] == 1.0
    assert result["party_roles"]["examples"][0]["label_before"] == "zero"
    assert result["party_roles"]["examples"][0]["label_after"] == "one"
    assert result["party_roles"]["examples"][0]["original"] == "Buyer pays |"
    assert classifier.inputs[0] == ["Buyer pays |"]
    assert (tmp_path / "tiny" / "counterfactual.json").exists()
    report = (tmp_path / "tiny" / "counterfactual.md").read_text()
    assert "Party roles" in report
    assert "Buyer pays" in report
    assert "1.000 [1.000, 1.000] / 0.000 [0.000, 0.000]" in report


def test_baseline_script_pickles_the_package_class(tmp_path, monkeypatch) -> None:
    """Running baseline.py as a script must not pickle the class as __main__.TfidfClassifier."""
    path = tmp_path / "model.joblib"
    monkeypatch.setattr(baseline, "main", lambda: TfidfClassifier().save(path))
    runpy.run_module("src.classification.baseline", run_name="__main__")
    assert b"__main__" not in path.read_bytes()
    assert type(joblib.load(path)) is TfidfClassifier
