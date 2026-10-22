"""Dense, TF-IDF, and keyword overlap clause indexes."""

from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from src.retrieval.constraints import extract_days, keep_days
from src.utils import get_device, resolve_path

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def words_of(text: str) -> set[str]:
    """Return the TP03 set of lowercase words after its three punctuation replacements."""
    return set(text.lower().replace("?", "").replace(".", "").replace(",", "").split())


def load_model(device: str | None = None):
    """Load MiniLM on the selected device."""
    return SentenceTransformer(MODEL_NAME, device=device or str(get_device()))


def embed(texts: list[str], model, cache_path: str | Path | None = None, batch_size: int = 64) -> np.ndarray:
    """Encode normalized float32 vectors, reusing a cache with the expected row count."""
    path = resolve_path(cache_path) if cache_path is not None else None
    if path is not None and path.exists():
        cached = np.load(path)
        if cached.ndim == 2 and cached.shape[0] == len(texts):
            return cached.astype(np.float32, copy=False)
    vectors = np.asarray(model.encode(texts, normalize_embeddings=True, batch_size=batch_size,
                                      show_progress_bar=True), dtype=np.float32)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, vectors)
    return vectors


def top_k(scores: np.ndarray, k: int) -> np.ndarray:
    """Return indices of the k highest scores in descending order."""
    return np.argsort(-scores)[:k]


class DenseIndex:
    """Cosine search over normalized MiniLM embeddings."""

    def __init__(self, embeddings: np.ndarray, model=None):
        self.embeddings = np.asarray(embeddings, dtype=np.float32)
        self.model = model

    def scores(self, query: str) -> np.ndarray:
        """Return cosine scores for a text query against all bank clauses."""
        if self.model is None:
            raise ValueError("DenseIndex requires a model for text queries")
        q = np.asarray(self.model.encode([query], normalize_embeddings=True)[0], dtype=np.float32)
        return self.embeddings @ q

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        """Return the highest scoring bank indices and cosine scores."""
        scores = self.scores(query)
        return [(int(index), float(scores[index])) for index in top_k(scores, k)]

    def search_vectors(self, Q: np.ndarray, k: int, chunk: int = 500) -> np.ndarray:
        """Search already encoded queries in chunks, returning bank indices."""
        results = []
        for start in range(0, len(Q), chunk):
            scores = Q[start:start + chunk] @ self.embeddings.T
            results.append(np.argsort(-scores, axis=1)[:, :k])
        return np.concatenate(results) if results else np.empty((0, min(k, len(self.embeddings))), dtype=int)


class TfidfIndex:
    """Cosine search with word unigrams and bigrams fitted on the clause bank."""

    def __init__(self, bank_texts: list[str]):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(bank_texts)

    def scores(self, query: str) -> np.ndarray:
        """Return TF-IDF cosine scores for all bank clauses."""
        q = self.vectorizer.transform([query])
        return (self.matrix @ q.T).toarray().ravel()

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        """Return highest scoring bank indices and cosine scores."""
        scores = self.scores(query)
        return [(int(index), float(scores[index])) for index in top_k(scores, k)]

    def search_many(self, queries: list[str], k: int, chunk: int = 500) -> np.ndarray:
        """Search text queries in chunks and return bank indices."""
        results = []
        for start in range(0, len(queries), chunk):
            q = self.vectorizer.transform(queries[start:start + chunk])
            scores = (q @ self.matrix.T).toarray()
            results.append(np.argsort(-scores, axis=1)[:, :k])
        return np.concatenate(results) if results else np.empty((0, min(k, self.matrix.shape[0])), dtype=int)


class OverlapIndex:
    """Exact TP03 set overlap using a binary bag of words."""

    def __init__(self, bank_texts: list[str]):
        self.vectorizer = CountVectorizer(analyzer=lambda text: sorted(words_of(text)), binary=True)
        self.matrix = self.vectorizer.fit_transform(bank_texts)

    def scores(self, query: str) -> np.ndarray:
        """Return word set intersection counts for all bank clauses."""
        q = self.vectorizer.transform([query])
        return (self.matrix @ q.T).toarray().ravel()

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        """Return highest scoring bank indices, breaking ties by index order."""
        scores = self.scores(query)
        return [(int(index), float(scores[index])) for index in np.argsort(-scores, kind="stable")[:k]]

    def search_many(self, queries: list[str], k: int, chunk: int = 500) -> np.ndarray:
        """Search text queries in chunks and return bank indices."""
        results = []
        for start in range(0, len(queries), chunk):
            q = self.vectorizer.transform(queries[start:start + chunk])
            scores = (q @ self.matrix.T).toarray()
            results.append(np.argsort(-scores, axis=1, kind="stable")[:, :k])
        return np.concatenate(results) if results else np.empty((0, min(k, self.matrix.shape[0])), dtype=int)


def search_with_days(index, query: str, bank_texts: list[str], k: int = 5, candidates: int = 200
                     ) -> tuple[list[tuple[int, float]], set[int]]:
    """Filter the highest scoring candidates to those sharing a query day duration."""
    days = extract_days(query)
    if not days:
        return index.search(query, k), days
    ranked = index.search(query, candidates)
    kept = set(keep_days([item[0] for item in ranked], bank_texts, days))
    return [item for item in ranked if item[0] in kept][:k], days
