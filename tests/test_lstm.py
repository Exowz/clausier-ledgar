"""Offline checks for the TP04 LSTM classifier."""

from collections import Counter

import numpy as np
import torch

from src.classification.lstm import (
    PAD,
    UNK,
    UNK_ID,
    LSTMClassifier,
    LSTMTextClassifier,
    build_vocab,
    collate_fn,
    encode,
    run_training,
    tokenize,
)
from src.classification.predict import load_classifier
from src.utils import load_json


def test_tp04_tokenization_and_vocabulary():
    """The regex and frequency ordering give reproducible token ids."""
    assert tokenize("Wall St. Bears Claw Back!") == ["wall", "st", "bears", "claw", "back"]
    vocab = build_vocab(Counter({"b": 3, "a": 3, "c": 5, "d": 1}))
    assert vocab == [PAD, UNK, "c", "a", "b"]
    assert encode("c unknown a", {word: index for index, word in enumerate(vocab)}) == [2, UNK_ID, 3]


def test_collate_pads_and_keeps_lengths_and_labels():
    """The packed LSTM receives true lengths and ordered labels."""
    batch = [(torch.tensor([2, 4, 5, 2, 3]), 0),
             (torch.tensor([6, 7, 8]), 1),
             (torch.tensor([2, 1, 5]), 2)]
    ids, lengths, labels = collate_fn(batch)
    assert ids.tolist() == [[2, 4, 5, 2, 3], [6, 7, 8, 0, 0], [2, 1, 5, 0, 0]]
    assert lengths.tolist() == [5, 3, 3]
    assert labels.tolist() == [0, 1, 2]


def test_lstm_output_shape_and_padding():
    """Padding cannot become a learned word embedding."""
    model = LSTMClassifier(vocab_size=10, emb_dim=8, hidden_dim=12, num_classes=4)
    ids = torch.tensor([[2, 3, 0], [4, 5, 6]])
    logits = model(ids, torch.tensor([2, 3]))
    assert logits.shape == (2, 4)
    assert torch.count_nonzero(model.emb.weight[0]).item() == 0


def test_training_saves_reloadable_standard_run(tmp_path):
    """A saved model reproduces ordered test probabilities in the shared run."""
    words = ["apple", "ocean", "rocket", "forest"]

    def split(per_class):
        texts = [f"{word} {word} bright {i % 3}" for word in words for i in range(per_class)]
        labels = np.repeat(np.arange(4), per_class).astype(np.int64)
        return texts, labels

    data = {"train": split(10), "validation": split(3), "test": split(3)}
    cfg = {"run_name": "tiny_lstm", "model_type": "lstm", "min_freq": 2, "max_tokens": 8,
           "emb_dim": 8, "hidden_dim": 12, "batch_size": 8, "eval_batch_size": 8,
           "lr": 0.01, "epochs": 2, "patience": 2, "grad_clip": 1.0,
           "glove": False, "seed": 42, "device": "cpu"}
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        metrics = run_training(cfg, data, words, tmp_path)
        run_dir = tmp_path / "tiny_lstm"
        for name in ("config.json", "metrics.json", "history.json", "training_curves.png",
                     "val_probs.npy", "test_probs.npy", "val_labels.npy", "test_labels.npy",
                     "model/model.pt", "model/vocab.json", "model/config.json"):
            assert (run_dir / name).exists(), name
        config = load_json(run_dir / "config.json")
        assert config["model_type"] == "lstm"
        assert config["n_train"] == 40
        assert config["vocab_size"] >= 6
        assert config["trainable_params"] == config["total_params"]
        assert config["truncated_train_share"] == 0
        assert 1 <= config["best_epoch"] <= 2
        assert len(load_json(run_dir / "history.json")) == 2
        assert metrics["test"]["n"] == 12
        expected = np.load(run_dir / "test_probs.npy")
        classifier = LSTMTextClassifier(run_dir / "model", device="cpu")
        probs = classifier.predict_proba(data["test"][0])
        assert probs.shape == (12, 4)
        assert probs.dtype == np.float32
        np.testing.assert_allclose(probs.sum(axis=1), 1, atol=1e-6)
        np.testing.assert_allclose(probs, expected, atol=1e-5)
        np.testing.assert_allclose(load_classifier(run_dir).predict_proba(data["test"][0]), expected, atol=1e-5)
    finally:
        torch.set_num_threads(previous_threads)
