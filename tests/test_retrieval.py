"""Small offline checks for clause retrieval."""

import numpy as np
import pytest

from src.retrieval.constraints import extract_days, keep_days
from src.retrieval.evaluate import bootstrap_mean, precision_at_k
from src.retrieval.index import (
    DenseIndex,
    OverlapIndex,
    TfidfIndex,
    embed,
    search_with_days,
    words_of,
)


class FakeModel:
    """Return fixed unit vectors and count encoding calls."""

    def __init__(self) -> None:
        self.calls = 0
        self.vectors = {
            "alpha": [1.0, 0.0],
            "beta": [0.0, 1.0],
            "mixed": [0.8, 0.6],
        }

    def encode(self, texts, normalize_embeddings=True, **kwargs):
        self.calls += 1
        assert normalize_embeddings
        return np.asarray([self.vectors[text] for text in texts], dtype=np.float32)


@pytest.mark.parametrize(("text", "expected"), [
    ("thirty (30) days", {30}),
    ("30-day notice", {30}),
    ("forty-five (45) calendar days", {45}),
    ("ten business days", {10}),
    ("sixty days", {60}),
    ("two (2) years", set()),
    ("Section 30", set()),
    ("within 30 days and then 90 days", {30, 90}),
    ("one hundred twenty days and three hundred sixty-five days", {120, 365}),
])
def test_extract_days(text, expected) -> None:
    assert extract_days(text) == expected


def test_keep_days_preserves_order() -> None:
    texts = ["30 days", "60 days", "thirty-day notice", "two years"]
    assert keep_days([2, 1, 3, 0], texts, {30}) == [2, 0]
    assert keep_days([2, 1, 3, 0], texts, set()) == [2, 1, 3, 0]


def test_words_of_course_overlap() -> None:
    assert len(words_of("the rent is due") & words_of("The rent is paid.")) == 3


def test_overlap_scores_are_set_intersections() -> None:
    bank = ["The rent is paid.", "rent, rent due?", "no overlap"]
    index = OverlapIndex(bank)
    assert index.scores("the rent is due").tolist() == [3, 2, 0]
    assert index.search_many(["the rent is due", "no overlap"], 2, chunk=1).tolist() == [[0, 1], [2, 0]]


def test_tfidf_identical_clause_is_first() -> None:
    bank = ["rent due today", "rent due tomorrow", "payment due tomorrow"]
    result = TfidfIndex(bank).search("rent due today", 1)
    assert result[0][0] == 0
    assert result[0][1] == pytest.approx(1.0)


def test_dense_search_and_chunked_search_vectors() -> None:
    model = FakeModel()
    d = np.asarray([[0, 1], [1, 0], [0.8, 0.6]], dtype=np.float32)
    index = DenseIndex(d, model)
    assert [item[0] for item in index.search("alpha", 3)] == [1, 2, 0]
    q = model.encode(["alpha", "beta", "mixed"])
    expected = np.argsort(-(q @ d.T), axis=1)[:, :2]
    np.testing.assert_array_equal(index.search_vectors(q, 2, chunk=1), expected)


def test_embed_cache_is_reused_and_wrong_length_recomputed(tmp_path) -> None:
    model = FakeModel()
    path = tmp_path / "vectors.npy"
    first = embed(["alpha", "beta"], model, path)
    np.testing.assert_array_equal(embed(["alpha", "beta"], model, path), first)
    assert model.calls == 1
    embed(["alpha"], model, path)
    assert model.calls == 2


def test_precision_and_bootstrap() -> None:
    labels = np.asarray([[1, 2, 1], [2, 1, 1]])
    np.testing.assert_array_equal(precision_at_k(labels, np.asarray([1, 2]), 2), [0.5, 0.5])
    mean, low, high = bootstrap_mean(np.asarray([0.0, 0.5, 1.0]), n_boot=100)
    assert mean == pytest.approx(0.5)
    assert low <= mean <= high


def test_search_with_days_filters_results() -> None:
    bank = ["termination with 60 days notice", "termination with 30-day notice", "30 days to pay"]
    results, days = search_with_days(OverlapIndex(bank), "termination with 30 days notice", bank)
    assert days == {30}
    assert [item[0] for item in results] == [1, 2]
