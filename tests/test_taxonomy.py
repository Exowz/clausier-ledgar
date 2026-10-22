"""Synthetic checks for overlapping-label evaluation."""

import json

import numpy as np
import pytest

from src.audit import taxonomy
from src.classification.run_io import save_run


def test_group_map_orders_groups_by_smallest_label_id() -> None:
    mapping, names = taxonomy.group_map(
        ["C", "A", "X", "B", "Y", "D"], [("A", "B"), ("C", "D")]
    )

    np.testing.assert_array_equal(mapping, [0, 1, 2, 1, 3, 0])
    assert names == ["C / D", "A / B", "X", "Y"]


def test_merge_probs_sums_columns_before_argmax() -> None:
    probs = np.array([[0.30, 0.26, 0.44], [0.10, 0.60, 0.30]])
    merged = taxonomy.merge_probs(probs, np.array([0, 0, 1]), 2)

    np.testing.assert_allclose(merged, [[0.56, 0.44], [0.70, 0.30]])
    np.testing.assert_allclose(merged.sum(axis=1), 1)
    assert merged[0].argmax() == 0
    assert probs[0].argmax() == 2


def test_evaluate_merge_recovers_within_pair_errors(tmp_path) -> None:
    names = ["A", "B", "C"]
    mapping, _ = taxonomy.group_map(names, [("A", "B")])
    probs = np.array([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1], [0.1, 0.1, 0.8]])
    labels = np.array([0, 1, 2])
    run_dir = tmp_path / "toy"
    save_run(run_dir, {}, probs, labels, probs, labels, names,
             dedup_mask_path=tmp_path / "missing.npy")

    result = taxonomy.evaluate_merge(run_dir, mapping, 2, np.array([True, True, True]))

    assert result["test"]["accuracy_before"][0] == pytest.approx(1 / 3)
    assert result["test"]["accuracy_after"][0] == 1.0
    assert result["test"]["share_errors_removed"] == 1.0


def test_main_writes_report_json_and_figure_from_saved_runs(tmp_path, monkeypatch, capsys) -> None:
    names = [name for pair in taxonomy.MERGED_PAIRS for name in pair] + ["Other"]
    labels = np.array([0, 1, 2, 3, 18, 0])
    first = np.eye(len(names))[np.array([1, 0, 3, 2, 18, 0])]
    second = np.eye(len(names))[np.array([0, 1, 2, 3, 18, 1])]
    mask_path = tmp_path / "mask.npy"
    np.save(mask_path, np.array([True, True, False, True, True, True]))
    monkeypatch.setattr(taxonomy, "DEDUP_MASK_PATH", mask_path)
    paths = [tmp_path / "tfidf", tmp_path / "legal_bert_long"]
    for path, probs in zip(paths, (first, second), strict=True):
        save_run(path, {}, probs, labels, probs, labels, names, dedup_mask_path=mask_path)

    out = tmp_path / "audit"
    figures = tmp_path / "figures"
    taxonomy.main(["--runs", *map(str, paths), "--out", str(out),
                   "--figures", str(figures), "--n-boot", "10"])

    markdown = (out / "taxonomy.md").read_text(encoding="utf-8")
    payload = json.loads((out / "taxonomy.json").read_text(encoding="utf-8"))
    assert "among the 10 most confused pairs of both" in markdown
    assert "McNemar p" in markdown
    assert "Applicable Laws / Governing Laws" in markdown
    assert payload["n_groups"] == 10
    assert (figures / "taxonomy_merge.png").is_file()
    assert markdown in capsys.readouterr().out
