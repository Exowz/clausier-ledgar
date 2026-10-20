"""Offline tests for the transformer training pipeline."""

import json

import numpy as np
import pytest
import torch
from transformers import (
    AutoModelForSequenceClassification,
    BertConfig,
    BertForSequenceClassification,
    BertTokenizerFast,
    get_linear_schedule_with_warmup,
)

from src.classification.dataset import make_loader, texts_to_dataset, tokenize_dataset
from src.classification.predict import TransformerClassifier, load_classifier
from src.classification.train import DEFAULTS, run_training


@pytest.fixture
def tiny_model_dir(tmp_path):
    """Save a four-class BERT and tokenizer made entirely from local data."""
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
    vocab += ["apple", "ocean", "rocket", "forest", "red", "blue", "green", "bright", "quiet", "near"]
    vocab += [f"word{i}" for i in range(45)]
    model_dir = tmp_path / "source_model"
    model_dir.mkdir()
    (model_dir / "vocab.txt").write_text("\n".join(vocab) + "\n", encoding="utf-8")
    tokenizer = BertTokenizerFast(vocab_file=str(model_dir / "vocab.txt"))
    tokenizer.save_pretrained(model_dir)
    torch.manual_seed(42)
    model = BertForSequenceClassification(BertConfig(
        vocab_size=len(vocab), hidden_size=32, num_hidden_layers=2,
        num_attention_heads=2, intermediate_size=37, num_labels=4,
    ))
    model.save_pretrained(model_dir)
    return model_dir


@pytest.fixture
def tiny_data():
    """Return separable synthetic clauses in four classes."""
    words = ["apple", "ocean", "rocket", "forest"]

    def split(per_class):
        texts = [f"{word} {word} bright word{i % 10}" for word in words for i in range(per_class)]
        labels = np.repeat(np.arange(4), per_class).astype(np.int64)
        return texts, labels

    return {"train": split(10), "validation": split(3), "test": split(3)}


def test_tokenization_truncates_without_padding_and_loader_pads(tiny_model_dir):
    tokenizer = BertTokenizerFast.from_pretrained(tiny_model_dir)
    texts = ["apple " * 20, "ocean"]
    dataset = texts_to_dataset(texts, np.array([0, 1]))
    tokenized = tokenize_dataset(dataset, tokenizer, max_length=8)

    assert tokenized.column_names == ["label", "input_ids", "token_type_ids", "attention_mask"]
    assert [len(row) for row in tokenized["input_ids"]] == [8, 3]
    batch = next(iter(make_loader(tokenized, tokenizer, batch_size=2, shuffle=False)))
    assert batch["input_ids"].shape == (2, 8)
    assert batch["attention_mask"][1].sum().item() == 3
    assert batch["labels"].tolist() == [0, 1]


def test_run_training_writes_reloadable_run(tiny_model_dir, tiny_data, tmp_path):
    config = {**DEFAULTS, "model_name": str(tiny_model_dir), "run_name": "tiny", "device": "cpu",
              "epochs": 2, "batch_size": 8, "eval_batch_size": 8, "max_length": 16,
              "num_workers": 0, "log_every": 2}
    metrics = run_training(config, tiny_data, ["apple", "ocean", "rocket", "forest"], tmp_path)
    run_dir = tmp_path / "tiny"

    for name in ("config.json", "metrics.json", "history.json", "training_curves.png", "val_probs.npy",
                 "test_probs.npy", "val_labels.npy", "test_labels.npy", "model/config.json"):
        assert (run_dir / name).exists(), name
    saved_config = json.loads((run_dir / "config.json").read_text())
    history = json.loads((run_dir / "history.json").read_text())
    assert saved_config["model_type"] == "transformer"
    assert saved_config["n_train"] == 40
    assert saved_config["trainable_params"] == saved_config["total_params"]
    assert len(history) == 2
    assert history[-1]["lr_end"] == pytest.approx(0)
    assert metrics["test"]["n"] == 12
    assert "test_dedup" not in metrics
    assert np.load(run_dir / "val_probs.npy").shape == (12, 4)
    assert np.load(run_dir / "test_labels.npy").shape == (12,)

    probs = TransformerClassifier(run_dir / "model", device="cpu").predict_proba(tiny_data["test"][0])
    assert probs.shape == (12, 4)
    assert probs.dtype == np.float32
    np.testing.assert_allclose(probs.sum(axis=1), 1, atol=1e-6)
    np.testing.assert_allclose(probs, np.load(run_dir / "test_probs.npy"), atol=1e-4)
    np.testing.assert_allclose(load_classifier(run_dir).predict_proba(tiny_data["test"][0]), probs, atol=1e-4)
    assert isinstance(AutoModelForSequenceClassification.from_pretrained(run_dir / "model"),
                      BertForSequenceClassification)


def test_linear_schedule_reaches_peak_and_zero():
    parameter = torch.nn.Parameter(torch.zeros(()))
    optimizer = torch.optim.AdamW([parameter], lr=3e-5)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=2, num_training_steps=10)
    for _ in range(2):
        optimizer.step()
        scheduler.step()
    assert scheduler.get_last_lr()[0] == pytest.approx(3e-5)
    for _ in range(8):
        optimizer.step()
        scheduler.step()
    assert scheduler.get_last_lr()[0] == pytest.approx(0)
