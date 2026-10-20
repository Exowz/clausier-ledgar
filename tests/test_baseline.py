"""Tests for the TF-IDF baseline and run artifacts."""

import numpy as np
import pytest

from src.classification import run_io
from src.classification.baseline import TfidfClassifier
from src.classification.run_io import load_run, save_run


def test_tfidf_classifier_missing_class_and_save_load(tmp_path) -> None:
    texts = [f"apple orchard fruit harvest {i}" for i in range(7)]
    texts += [f"ocean wave salt water {i}" for i in range(7)]
    texts += [f"rocket orbit space planet {i}" for i in range(7)]
    labels = np.repeat(np.arange(3), 7)
    model = TfidfClassifier(n_classes=4, min_df=1).fit(texts, labels)

    probs = model.predict_proba(texts)
    assert probs.shape == (21, 4)
    np.testing.assert_allclose(probs.sum(axis=1), 1)
    np.testing.assert_array_equal(probs[:, 3], 0)
    assert np.mean(probs.argmax(axis=1) == labels) == 1.0

    path = tmp_path / "model.joblib"
    model.save(path)
    np.testing.assert_array_equal(TfidfClassifier.load(path).predict_proba(texts), probs)


def test_save_load_run_with_missing_dedup_mask(tmp_path, capsys) -> None:
    rng = np.random.default_rng(42)
    val_probs = rng.dirichlet(np.ones(3), size=4)
    test_probs = rng.dirichlet(np.ones(3), size=5)
    val_labels = np.array([0, 1, 2, 0])
    test_labels = np.array([1, 0, 2, 1, 0])
    run_dir = tmp_path / "run"

    metrics = save_run(
        run_dir, {"run_name": "run", "model_type": "tfidf"}, val_probs, val_labels,
        test_probs, test_labels, ["a", "b", "c"], extra_metrics={"train_time_s": 1.5},
        dedup_mask_path=tmp_path / "missing.npy",
    )
    loaded = load_run(run_dir)

    assert "test_dedup" not in metrics
    assert "warning" in capsys.readouterr().out.lower()
    assert loaded["metrics"] == metrics
    assert loaded["config"]["git_commit"] is None or isinstance(loaded["config"]["git_commit"], str)
    assert loaded["val_probs"].dtype == np.float32
    assert loaded["test_labels"].dtype == np.int64
    np.testing.assert_allclose(loaded["val_probs"], val_probs, rtol=1e-7)
    np.testing.assert_array_equal(loaded["test_labels"], test_labels)


def test_save_run_applies_dedup_mask(tmp_path) -> None:
    mask_path = tmp_path / "mask.npy"
    np.save(mask_path, np.array([True, False, True]))
    probs = np.array([[0.9, 0.1], [0.9, 0.1], [0.1, 0.9]])
    labels = np.array([0, 1, 1])

    metrics = save_run(
        tmp_path / "run", {"run_name": "run", "model_type": "tfidf"},
        probs, labels, probs, labels, ["a", "b"], dedup_mask_path=mask_path,
    )

    assert metrics["test_dedup"]["n"] == 2
    assert metrics["test_dedup"]["accuracy"] == pytest.approx(1.0)


def test_git_commit_returns_none_without_git(monkeypatch) -> None:
    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(run_io.subprocess, "run", missing_git)

    assert run_io.git_commit() is None
