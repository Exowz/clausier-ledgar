"""Synthetic checks for final result tables and paired comparisons."""

import json

import numpy as np
import pytest

from src.classification import results
from src.classification.run_io import save_run


def make_run(outputs, name, mask_path, val_f1, test_f1, *, config=None):
    """Save a small run with controlled selection scores and real prediction files."""
    labels = np.array([0, 1, 0, 1, 0, 1])
    predictions = labels.copy() if name != "tfidf" else np.array([0, 0, 0, 1, 0, 1])
    probs = np.eye(2)[predictions] * 0.8 + 0.1
    run_dir = outputs / name
    metrics = save_run(run_dir, {"run_name": name, **(config or {})}, probs, labels,
                       probs, labels, ["zero", "one"], dedup_mask_path=mask_path)
    metrics["validation"]["macro_f1"] = val_f1
    metrics["test"]["macro_f1"] = test_f1
    (run_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    return run_dir


@pytest.fixture
def runs(tmp_path):
    outputs = tmp_path / "outputs"
    mask_path = outputs / "data" / "test_dedup_mask.npy"
    mask_path.parent.mkdir(parents=True)
    np.save(mask_path, np.array([True, False, True, True, True, True]))
    make_run(outputs, "tfidf", mask_path, 0.75, 0.95)
    make_run(outputs, "legal_bert", mask_path, 0.82, 0.89,
             config={"best_epoch": 3, "trainable_params": 1000, "total_params": 2000,
                     "train_memory_gb_estimate": 1.25, "train_time_s": 120})
    (outputs / "legal_bert" / "history.json").write_text(json.dumps([{}, {}, {}, {}]), encoding="utf-8")
    make_run(outputs, "legal_bert_long", mask_path, 0.84, 0.81,
             config={"best_epoch": 5, "trainable_params": 1200, "total_params": 2400,
                     "train_memory_gb_estimate": 1.5, "train_time_s": 300})
    (outputs / "legal_bert_long" / "history.json").write_text(
        json.dumps([{}, {}, {}, {}, {}, {}]), encoding="utf-8")
    return outputs, mask_path


def test_present_runs_and_validation_selection(runs):
    outputs, _ = runs
    make_run(outputs, "legal_bert_smoke", outputs / "data" / "test_dedup_mask.npy", 1.0, 1.0)

    assert results.present_runs(outputs) == ["tfidf", "legal_bert", "legal_bert_long"]
    assert results.best_legal_bert(outputs) == "legal_bert_long"
    assert results.best_legal_bert(outputs / "missing") is None


def test_results_and_lora_tables_read_run_artifacts(runs):
    outputs, _ = runs
    names = results.present_runs(outputs)

    rows = results.results_table(names, outputs).set_index("model")
    assert rows.loc["TF-IDF + logistic regression", "best_epoch"] == ""
    assert rows.loc["TF-IDF + logistic regression", "train_time_min"] == ""
    assert rows.loc["Legal-BERT (4 epochs)", "best_epoch"] == 3
    assert rows.loc["Legal-BERT (4 epochs)", "val_macro_f1"] == pytest.approx(0.82)
    assert rows.loc["Legal-BERT (4 epochs)", "train_time_min"] == pytest.approx(2.0)

    lora = results.lora_table(names, outputs).set_index("model")
    assert list(lora.index) == ["Legal-BERT (4 epochs)", "Legal-BERT (up to 10 epochs)"]
    assert lora.loc["Legal-BERT (4 epochs)", "trainable_share"] == pytest.approx(50.0)
    assert lora.loc["Legal-BERT (4 epochs)", "time_per_epoch_min"] == pytest.approx(0.5)
    assert lora.loc["Legal-BERT (up to 10 epochs)", "time_per_epoch_min"] == pytest.approx(5 / 6)


def test_pairs_use_present_models_and_best_legal_bert(runs):
    outputs, _ = runs
    assert results.pairs(outputs) == [("legal_bert_long", "tfidf", "main comparison")]


def test_print_best_outputs_only_run_name(runs, capsys):
    outputs, _ = runs
    results.main(["--outputs", str(outputs), "--print-best"])
    assert capsys.readouterr().out == "legal_bert_long\n"


def test_main_writes_tables_pair_results_and_figure(runs, tmp_path, capsys):
    outputs, _ = runs
    out = tmp_path / "reports"

    results.main(["--outputs", str(outputs), "--out", str(out), "--n-boot", "10"])

    markdown = (out / "results.md").read_text(encoding="utf-8")
    data = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert "## Reference: LexGLUE (published)" in markdown
    assert "Best Legal-BERT run, chosen on validation macro-F1: Legal-BERT (up to 10 epochs)." in markdown
    assert "main comparison" in markdown
    assert len(data["results_table"]) == 3
    assert len(data["pairs"]) == 1
    assert data["reference_lexglue"][2] == {"model": "Legal-BERT", "micro_f1": 88.2, "macro_f1": 83.0}
    assert (out / "figures" / "model_comparison.png").is_file()
    assert (out / "audit" / "compare_legal_bert_long_vs_tfidf.json").is_file()
    assert (out / "audit" / "compare_legal_bert_long_vs_tfidf.md").is_file()
    captured = capsys.readouterr().out
    assert "skipped lstm: not found" in captured
    assert markdown in captured
