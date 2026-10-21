"""Bootstrap intervals for metrics on classifier predictions."""

import numpy as np
from sklearn.metrics import accuracy_score, f1_score


def macro_f1(y_true: np.ndarray, pred: np.ndarray, labels: np.ndarray) -> float:
    """Compute macro-F1 over the given true label IDs."""
    return float(f1_score(y_true, pred, average="macro", labels=labels, zero_division=0))


def bootstrap_ci(
    y_true: np.ndarray, pred: np.ndarray, metric: str = "macro_f1", n_boot: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Return the observed metric and its 2.5 and 97.5 bootstrap percentiles."""
    truth = np.asarray(y_true)
    predictions = np.asarray(pred)
    if truth.ndim != 1 or predictions.shape != truth.shape or len(truth) == 0:
        raise ValueError("y_true and pred must be nonempty one-dimensional arrays of equal length")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")
    if metric not in {"macro_f1", "accuracy"}:
        raise ValueError(f"Unknown metric: {metric}")
    def score(indices: np.ndarray) -> float:
        if metric == "accuracy":
            return float(accuracy_score(truth[indices], predictions[indices]))
        return macro_f1(truth[indices], predictions[indices], np.unique(truth[indices]))

    observed = score(np.arange(len(truth)))
    rng = np.random.default_rng(seed)
    samples = np.empty(n_boot)
    if metric == "accuracy":
        correct = truth == predictions
        for start in range(0, n_boot, 100):
            end = min(start + 100, n_boot)
            chosen = rng.integers(0, len(truth), size=(end - start, len(truth)))
            samples[start:end] = correct[chosen].mean(axis=1)
    else:
        for index in range(n_boot):
            samples[index] = score(rng.integers(0, len(truth), size=len(truth)))
    low, high = np.percentile(samples, [2.5, 97.5])
    return observed, float(low), float(high)
