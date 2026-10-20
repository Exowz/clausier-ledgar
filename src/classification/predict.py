"""Load saved classifiers behind a shared probability interface."""

from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.classification.baseline import TfidfClassifier
from src.utils import get_device, load_json, resolve_path


class TransformerClassifier:
    """Predict class probabilities with a saved transformer classifier."""

    def __init__(
        self, model_dir: str | Path, device: str | None = None, batch_size: int = 64, max_length: int = 256,
    ) -> None:
        """Load a saved model and tokenizer onto the requested device."""
        model_dir = resolve_path(model_dir)
        self.device = get_device(device)
        self.batch_size = batch_size
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(self.device)
        self.model.eval()

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Return float32 probabilities in input order."""
        if not texts:
            return np.empty((0, self.model.config.num_labels), dtype=np.float32)
        batches = []
        with torch.no_grad():
            for start in range(0, len(texts), self.batch_size):
                inputs = self.tokenizer(
                    texts[start:start + self.batch_size], truncation=True,
                    max_length=self.max_length, padding=True, return_tensors="pt",
                ).to(self.device)
                logits = self.model(**inputs).logits
                batches.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
        return np.concatenate(batches).astype(np.float32, copy=False)


def load_classifier(run_dir: str | Path):
    """Load a TF-IDF or transformer classifier from a standard run directory."""
    run_dir = resolve_path(run_dir)
    config = load_json(run_dir / "config.json")
    if config["model_type"] == "tfidf":
        return TfidfClassifier.load(run_dir / "model.joblib")
    if config["model_type"] == "transformer":
        return TransformerClassifier(run_dir / "model", max_length=config["max_length"])
    raise ValueError(f"Unknown model_type: {config['model_type']}")
