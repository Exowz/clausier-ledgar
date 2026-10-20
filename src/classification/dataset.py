"""Tokenize texts and build dynamically padded classifier batches."""

import numpy as np
import torch
from datasets import Dataset
from torch.utils.data import DataLoader
from transformers import DataCollatorWithPadding


def texts_to_dataset(texts: list[str], labels: np.ndarray) -> Dataset:
    """Return a dataset with text and integer label columns."""
    return Dataset.from_dict({"text": texts, "label": np.asarray(labels, dtype=np.int64).tolist()})


def tokenize_dataset(ds: Dataset, tokenizer, max_length: int) -> Dataset:
    """Tokenize without padding and keep labels for the collator."""
    def tokenize_batch(batch):
        return tokenizer(batch["text"], truncation=True, max_length=max_length)

    return ds.map(tokenize_batch, batched=True, remove_columns=["text"])


def make_loader(
    tok_ds: Dataset, tokenizer, batch_size: int, shuffle: bool, seed: int = 42, num_workers: int = 0,
) -> DataLoader:
    """Build a dynamically padded loader with deterministic shuffling."""
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        tok_ds, batch_size=batch_size, shuffle=shuffle,
        collate_fn=DataCollatorWithPadding(tokenizer), generator=generator, num_workers=num_workers,
    )
