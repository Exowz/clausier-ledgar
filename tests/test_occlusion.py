"""Tests for word erasure and its faithfulness check."""

import numpy as np

from src.audit.occlusion import comprehensiveness, explain, words_with_spans


class KeywordClassifier:
    """Assign the first class only when the word terminate is present."""

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        return np.asarray([[0.9, 0.1, 0.0] if "terminate" in text.split()
                           else [0.1, 0.9, 0.0] for text in texts])


def test_words_with_spans_slice_original_text() -> None:
    text = "  Terminate\tthis\n agreement  "
    spans = words_with_spans(text)
    assert [word for word, _, _ in spans] == ["Terminate", "this", "agreement"]
    assert all(text[start:end] == word for word, start, end in spans)


def test_explain_identifies_keyword_and_normalizes_whitespace() -> None:
    result = explain(KeywordClassifier(), "we\tterminate  this agreement")
    assert result["label"] == 0
    assert result["probability"] == 0.9
    assert result["words"][1]["word"] == "terminate"
    assert result["words"][1]["importance"] == 0.8
    assert all(abs(row["importance"]) < 1e-10 for i, row in enumerate(result["words"]) if i != 1)


def test_comprehensiveness_top_word_beats_random() -> None:
    texts = ["terminate " + " ".join(f"word{i}" for i in range(20)) for _ in range(20)]
    result = comprehensiveness(KeywordClassifier(), texts, k=1)
    assert result["mean_top_k_drop"] > result["mean_random_drop"]
    assert result["top_k_changed_share"] > result["random_changed_share"]
    assert len(result["top_k_drops"]) == len(texts)
