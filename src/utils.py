"""Shared seed, device, path, and file utilities."""

import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml

PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
SEED: int = 42


def set_seed(seed: int = SEED) -> None:
    """Seed Python, NumPy, PyTorch, and all CUDA devices; set PYTHONHASHSEED."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_device(prefer: str | None = None) -> torch.device:
    """Use a preferred available device, or detect CUDA, MPS, then CPU."""
    if prefer not in {None, "cuda", "mps", "cpu"}:
        raise ValueError(f"Unknown device: {prefer}")

    cuda_available = torch.cuda.is_available()
    mps_backend = getattr(torch.backends, "mps", None)
    mps_available = mps_backend is not None and getattr(mps_backend, "is_available", lambda: False)()

    if prefer == "cpu":
        return torch.device("cpu")
    if prefer == "cuda" and cuda_available:
        return torch.device("cuda")
    if prefer == "mps" and mps_available:
        return torch.device("mps")
    if cuda_available:
        return torch.device("cuda")
    if mps_available:
        return torch.device("mps")
    return torch.device("cpu")


def resolve_path(path: str | Path) -> Path:
    """Return an absolute path, resolving relative paths from PROJECT_ROOT."""
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def ensure_dir(path: str | Path) -> Path:
    """Create a directory and its parents, then return its absolute path."""
    directory = resolve_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _json_default(value: Any) -> Any:
    if isinstance(value, np.integer | np.floating):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def save_json(obj: Any, path: str | Path) -> None:
    """Save JSON with indentation, converting NumPy numbers and arrays."""
    output_path = resolve_path(path)
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(obj, file, indent=2, sort_keys=False, default=_json_default)


def load_json(path: str | Path) -> Any:
    """Load JSON from a path relative to the project or an absolute path."""
    with resolve_path(path).open(encoding="utf-8") as file:
        return json.load(file)


def load_yaml(path: str | Path) -> dict:
    """Load a YAML mapping, returning an empty dict for an empty file."""
    with resolve_path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def timestamp() -> str:
    """Return the current time in YYYYMMDD-HHMMSS format for logs."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")
