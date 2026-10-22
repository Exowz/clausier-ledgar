"""Synthetic checks for calibration, abstention, and conformal reports."""

import json

import numpy as np
import pytest

from src.audit import calibration
from src.classification.run_io import save_run


def test_reliability_and_ece_use_bin_accuracy() -> None:
    probs = np.array([[0.5, 0.5]] * 4 + [[0.75, 0.25]] * 4)
    labels = np.array([0, 0, 1, 1, 0, 0, 0, 1])

    table = calibration.reliability(probs, labels, n_bins=4)

    assert len(table) == 4
    assert table["n"].sum() == 8
    assert table.loc[2, "accuracy"] == pytest.approx(0.5)
    assert np.isnan(table.loc[0, "accuracy"])
    assert calibration.ece(probs, labels, n_bins=4) == pytest.approx(0)
    assert calibration.ece(np.array([[0.9, 0.1]] * 4), np.array([0, 0, 1, 1])) == pytest.approx(0.4)


def test_temperature_preserves_predictions_and_normalizes() -> None:
    probs = np.array([[0.8, 0.2], [0.1, 0.9], [0.3, 0.7]])

    np.testing.assert_allclose(calibration.apply_temperature(probs, 1), probs, atol=1e-6)
    for temperature in (0.5, 3):
        scaled = calibration.apply_temperature(probs, temperature)
        np.testing.assert_allclose(scaled.sum(axis=1), 1)
        np.testing.assert_array_equal(scaled.argmax(axis=1), probs.argmax(axis=1))


def test_fit_temperature_softens_overconfident_probabilities() -> None:
    labels = np.array([0] * 70 + [1] * 30)
    probs = np.tile([0.95, 0.05], (100, 1))

    temperature = calibration.fit_temperature(probs, labels)

    assert temperature > 1
    assert calibration.nll(calibration.apply_temperature(probs, temperature), labels) < calibration.nll(probs, labels)


def test_abstention_uses_smallest_eligible_confidence() -> None:
    probs = np.array([[0.9, 0.1], [0.9, 0.1], [0.6, 0.4], [0.55, 0.45]])
    labels = np.array([0, 0, 1, 1])

    threshold = calibration.abstention_threshold(probs, labels, target_accuracy=0.95)
    curve = calibration.coverage_curve(probs, labels, n_points=3)

    assert threshold == pytest.approx(0.9)
    assert np.mean(labels[probs.max(axis=1) >= threshold] == 0) >= 0.95
    assert list(curve.columns) == ["threshold", "coverage", "accuracy"]
    assert np.isnan(curve.iloc[-1]["accuracy"])
    assert calibration.abstention_threshold(probs, np.array([1, 1, 1, 1])) == 1.0


def test_split_conformal_coverage_on_exchangeable_data() -> None:
    rng = np.random.default_rng(42)
    probs = rng.dirichlet(np.ones(3), size=10_000)
    labels = np.array([rng.choice(3, p=row) for row in probs])

    q_hat = calibration.conformal_threshold(probs[:5000], labels[:5000], alpha=0.1)
    sets = calibration.prediction_sets(probs[5000:], q_hat)
    coverage = np.mean([label in members for label, members in zip(labels[5000:], sets, strict=True)])

    assert 0.88 <= coverage <= 0.92


def test_calibrate_run_and_cli_write_reports(tmp_path, capsys) -> None:
    probs = np.array([[0.85, 0.10, 0.05], [0.05, 0.90, 0.05], [0.05, 0.10, 0.85],
                      [0.45, 0.40, 0.15], [0.20, 0.60, 0.20], [0.20, 0.30, 0.50]])
    labels = np.array([0, 1, 2, 1, 1, 2])
    run_dirs = []
    for name in ("small_a", "small_b"):
        path = tmp_path / name
        save_run(path, {"run_name": name}, probs, labels, probs, labels,
                 ["alpha", "beta", "gamma"], dedup_mask_path=tmp_path / "missing.npy")
        run_dirs.append(path)

    result = calibration.calibrate_run(run_dirs[0])

    assert set(result) >= {"run", "temperature", "calibration", "abstention", "conformal", "coverage_curve"}
    assert set(result["calibration"]) == {"validation", "test"}
    assert set(result["abstention"]) >= {"threshold", "test_coverage", "test_accuracy", "test_macro_f1",
                                         "share_sent_to_human", "no_abstention"}
    assert set(result["conformal"]) >= {"q_hat", "test_coverage", "mean_set_size", "set_size_distribution",
                                        "coverage_per_set_size", "top_10_pairs"}
    json.dumps(result, allow_nan=False)

    out = tmp_path / "audit"
    figures = tmp_path / "figures"
    calibration.main(["--run", *map(str, run_dirs), "--out", str(out), "--figures", str(figures)])

    for name in ("small_a", "small_b"):
        report = out / name / "calibration.md"
        assert report.is_file()
        assert "# Calibration and abstention:" in report.read_text(encoding="utf-8")
        assert "Most frequent two-label sets" in report.read_text(encoding="utf-8")
        assert (out / name / "calibration.json").is_file()
        assert (figures / f"{name}_reliability.png").is_file()
        assert (figures / f"{name}_coverage.png").is_file()
    assert (figures / "coverage_comparison.png").is_file()
    assert "# Calibration and abstention: small_a" in capsys.readouterr().out
