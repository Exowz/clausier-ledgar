"""Shared classification metrics for all LEDGAR models."""

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, log_loss, precision_recall_fscore_support


def confusion(probs_or_preds: np.ndarray, y_true: np.ndarray, n_classes: int = 100) -> np.ndarray:
    """Return a fixed-size confusion matrix from probabilities or predictions."""
    values = np.asarray(probs_or_preds)
    predictions = values.argmax(axis=1) if values.ndim == 2 else values
    return confusion_matrix(y_true, predictions, labels=range(n_classes))


def top_confused_pairs(cm: np.ndarray, label_names: list[str], k: int = 20) -> list[dict]:
    """Return the k most frequent bidirectional off-diagonal label pairs."""
    pairs = []
    for a in range(len(label_names)):
        for b in range(a + 1, len(label_names)):
            a_as_b = int(cm[a, b])
            b_as_a = int(cm[b, a])
            total = a_as_b + b_as_a
            if total:
                pairs.append({
                    "a": a, "b": b, "name_a": label_names[a], "name_b": label_names[b],
                    "a_as_b": a_as_b, "b_as_a": b_as_a, "total": total,
                })
    return sorted(pairs, key=lambda pair: (-pair["total"], pair["a"], pair["b"]))[:k]


def evaluate(
    probs: np.ndarray, y_true: np.ndarray, label_names: list[str], mask: np.ndarray | None = None,
    k_confused: int = 20,
) -> dict:
    """Evaluate probabilities, optionally on a masked subset, across all classes."""
    probs = np.asarray(probs)
    y_true = np.asarray(y_true)
    if mask is not None:
        probs = probs[mask]
        y_true = y_true[mask]
    labels = range(len(label_names))
    predictions = probs.argmax(axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, predictions, labels=labels, zero_division=0,
    )
    per_class = [
        {
            "label": label, "name": name, "precision": float(precision[label]),
            "recall": float(recall[label]), "f1": float(f1[label]), "support": int(support[label]),
        }
        for label, name in enumerate(label_names)
    ]
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "micro_f1": float(f1_score(y_true, predictions, labels=labels, average="micro", zero_division=0)),
        "macro_f1": float(f1_score(y_true, predictions, labels=labels, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, predictions, labels=labels, average="weighted", zero_division=0)),
        "cross_entropy": float(log_loss(y_true, probs, labels=labels)),
        "per_class": per_class,
        "top_confused": top_confused_pairs(confusion(predictions, y_true, len(label_names)), label_names, k_confused),
    }
