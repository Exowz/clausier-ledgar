"""Read and write the shared classifier run format."""

import subprocess
from pathlib import Path

import numpy as np

from src.classification.metrics import evaluate
from src.utils import ensure_dir, load_json, resolve_path, save_json


def git_commit() -> str | None:
    """Return the short current git commit, or None outside a git checkout."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=resolve_path("."),
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def save_run(
    run_dir: str | Path, config: dict, val_probs: np.ndarray, val_labels: np.ndarray,
    test_probs: np.ndarray, test_labels: np.ndarray, label_names: list[str],
    extra_metrics: dict | None = None,
    dedup_mask_path: str | Path = "outputs/data/test_dedup_mask.npy",
) -> dict:
    """Save configuration, probabilities, labels, and full and deduplicated metrics."""
    output = ensure_dir(run_dir)
    val_probs = np.asarray(val_probs, dtype=np.float32)
    test_probs = np.asarray(test_probs, dtype=np.float32)
    val_labels = np.asarray(val_labels, dtype=np.int64)
    test_labels = np.asarray(test_labels, dtype=np.int64)
    metrics = {
        "validation": evaluate(val_probs, val_labels, label_names),
        "test": evaluate(test_probs, test_labels, label_names),
    }
    mask_path = resolve_path(dedup_mask_path)
    if mask_path.exists():
        mask = np.load(mask_path)
        if len(mask) == len(test_labels):
            metrics["test_dedup"] = evaluate(test_probs, test_labels, label_names, mask=mask.astype(bool))
        else:
            print(f"Warning: dedup mask length differs from test labels: {mask_path}")
    else:
        print(f"Warning: dedup mask is missing: {mask_path}")
    metrics["label_names"] = label_names
    if extra_metrics:
        metrics.update(extra_metrics)
    save_json({**config, "git_commit": git_commit()}, output / "config.json")
    save_json(metrics, output / "metrics.json")
    np.save(output / "val_probs.npy", val_probs)
    np.save(output / "test_probs.npy", test_probs)
    np.save(output / "val_labels.npy", val_labels)
    np.save(output / "test_labels.npy", test_labels)
    return metrics


def load_run(run_dir: str | Path) -> dict:
    """Load the configuration, metrics, probabilities, and labels of a run."""
    output = resolve_path(run_dir)
    return {
        "config": load_json(output / "config.json"),
        "metrics": load_json(output / "metrics.json"),
        "val_probs": np.load(output / "val_probs.npy"),
        "test_probs": np.load(output / "test_probs.npy"),
        "val_labels": np.load(output / "val_labels.npy"),
        "test_labels": np.load(output / "test_labels.npy"),
    }
