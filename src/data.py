"""LEDGAR loading, train/test overlap, and clause slices.

Family is the category with the most case-insensitive keyword hits, with ties
following FAMILY_PATTERNS order. Jurisdiction uses capitalized names and the
priority Delaware, New York, other US state, non-US place, none. Token lengths
use [0, 64), [64, 128), [128, max_len), and [max_len, infinity).
"""

import re

import numpy as np
import pandas as pd
from datasets import DatasetDict, load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import AutoTokenizer

DATASET_NAME = "coastalcph/lex_glue"
DATASET_CONFIG = "ledgar"
SPLITS = ("train", "validation", "test")

FAMILY_PATTERNS: dict[str, list[str]] = {
    "credit": [r"\bborrower\b", r"\blender\b", r"\bloan\b", r"\bcredit agreement\b", r"\blenders\b"],
    "employment": [r"\bemployee\b", r"\bemployer\b", r"\bexecutive\b", r"\bemployment\b"],
    "license": [r"\blicensor\b", r"\blicensee\b", r"\blicense agreement\b"],
    "lease": [r"\blandlord\b", r"\btenant\b", r"\blessor\b", r"\blessee\b", r"\bpremises\b"],
    "m&a": [
        r"\bmerger\b", r"\bshareholders?\b", r"\bstockholders?\b", r"\bacquisition\b", r"\bpurchaser\b"
    ],
}
_FAMILY_REGEXES = {family: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
                   for family, patterns in FAMILY_PATTERNS.items()}

US_STATES: list[str] = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
]
NON_US_PATTERNS: list[str] = [
    "England", "Wales", "United Kingdom", "Scotland", "Ireland", "Canada", "Ontario", "Quebec",
    "British Columbia", "Cayman Islands", "Bermuda", "British Virgin Islands", "Luxembourg", "Netherlands",
    "Germany", "France", "Switzerland", "Israel", "Hong Kong", "Singapore", "China",
    "People's Republic of China", "Japan", "India", "Australia", "Mexico", "Brazil",
]
_DELAWARE_RE = re.compile(r"\bDelaware\b")
_NEW_YORK_RE = re.compile(r"\bNew York\b")
_OTHER_US_REGEXES = [re.compile(rf"\b{re.escape(name)}\b") for name in US_STATES
                     if name not in {"Delaware", "New York"}]
_NON_US_REGEXES = [re.compile(rf"\b{re.escape(name)}\b") for name in NON_US_PATTERNS]
_NORMALIZE_RE = re.compile(r"[\W_]+")
LENGTH_BINS = ("<64", "64-127", "128-255", ">=256 (truncated)")


def load_ledgar() -> DatasetDict:
    """Load the cached LEDGAR dataset with its train, validation, and test splits."""
    return load_dataset(DATASET_NAME, DATASET_CONFIG)


def get_label_names() -> list[str]:
    """Return LEDGAR label names in numeric label ID order."""
    return list(load_ledgar()["train"].features["label"].names)


def load_split(split: str, n: int | None = None, seed: int = 42) -> tuple[list[str], np.ndarray]:
    """Return texts and integer labels, optionally using a seeded random subset."""
    if split not in SPLITS:
        raise ValueError(f"Unknown split: {split}")
    dataset = load_ledgar()[split]
    if n is not None:
        dataset = dataset.shuffle(seed=seed).select(range(n))
    return list(dataset["text"]), np.asarray(dataset["label"], dtype=np.int64)


def normalize_text(text: str) -> str:
    """Lowercase, replace each non-alphanumeric run with one space, and strip."""
    return _NORMALIZE_RE.sub(" ", text.lower()).strip()


def find_overlap(
    train_texts: list[str], test_texts: list[str], near_threshold: float = 0.9, chunk_size: int = 1000
) -> pd.DataFrame:
    """Find exact and TF-IDF near duplicates using chunked sparse cosine similarities."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    normalized_train = [normalize_text(text) for text in train_texts]
    normalized_test = [normalize_text(text) for text in test_texts]
    train_lookup = {}
    for index, text in enumerate(normalized_train):
        train_lookup.setdefault(text, index)
    exact = np.fromiter((text in train_lookup for text in normalized_test), dtype=bool, count=len(test_texts))
    max_sim = np.zeros(len(test_texts), dtype=float)
    nearest = np.full(len(test_texts), 0 if normalized_train else -1, dtype=int)

    if normalized_train and normalized_test and any(normalized_train):
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        train_matrix = vectorizer.fit_transform(normalized_train)
        for start in range(0, len(normalized_test), chunk_size):
            end = min(start + chunk_size, len(normalized_test))
            test_matrix = vectorizer.transform(normalized_test[start:end])
            similarities = (test_matrix @ train_matrix.T).tocsr()
            for offset in range(end - start):
                row_start, row_end = similarities.indptr[offset:offset + 2]
                if row_start == row_end:
                    continue
                best = row_start + int(np.argmax(similarities.data[row_start:row_end]))
                max_sim[start + offset] = similarities.data[best]
                nearest[start + offset] = similarities.indices[best]

    for index, is_exact in enumerate(exact):
        if is_exact:
            nearest[index] = train_lookup[normalized_test[index]]

    near = (max_sim >= near_threshold) & ~exact
    return pd.DataFrame({
        "exact_dup": exact,
        "max_sim": max_sim,
        "nearest_train_idx": nearest,
        "near_dup": near,
        "keep": ~(exact | near),
    })


def contract_family(text: str) -> str:
    """Return the family with most keyword hits, using dictionary order for ties."""
    counts = {family: sum(len(regex.findall(text)) for regex in patterns)
              for family, patterns in _FAMILY_REGEXES.items()}
    winner = max(counts, key=counts.get)
    return winner if counts[winner] else "other"


def jurisdiction(text: str) -> str:
    """Classify capitalized place mentions by the documented priority order."""
    if _DELAWARE_RE.search(text):
        return "delaware"
    if _NEW_YORK_RE.search(text):
        return "new_york"
    if any(regex.search(text) for regex in _OTHER_US_REGEXES):
        return "other_us"
    if any(regex.search(text) for regex in _NON_US_REGEXES):
        return "non_us"
    return "none"


def length_bin(n_tokens: int, max_len: int = 256) -> str:
    """Assign a token count to the four bins defined by 64, 128, and max_len."""
    if n_tokens < 64:
        return "<64"
    if n_tokens < 128:
        return "64-127"
    if n_tokens < max_len:
        return f"128-{max_len - 1}"
    return f">={max_len} (truncated)"


def count_tokens(texts: list[str], tokenizer_name: str, batch_size: int = 1000) -> np.ndarray:
    """Count untruncated tokens, including special tokens, in tokenizer batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
    counts = np.empty(len(texts), dtype=np.int32)
    for start in range(0, len(texts), batch_size):
        batch = tokenizer(texts[start:start + batch_size], truncation=False)["input_ids"]
        counts[start:start + len(batch)] = [len(ids) for ids in batch]
    return counts


def slice_frame(texts: list[str], n_tokens: np.ndarray | None = None, max_len: int = 256) -> pd.DataFrame:
    """Return family, jurisdiction, and optional token length bin for each text."""
    if n_tokens is not None and len(n_tokens) != len(texts):
        raise ValueError("n_tokens and texts must have the same length")
    columns = {
        "family": [contract_family(text) for text in texts],
        "jurisdiction": [jurisdiction(text) for text in texts],
    }
    if n_tokens is not None:
        columns["length_bin"] = [length_bin(int(count), max_len) for count in n_tokens]
    return pd.DataFrame(columns)
