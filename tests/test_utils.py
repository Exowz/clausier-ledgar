"""Tests for shared project utilities."""

import os
import random
import re

import numpy as np
import pytest
import torch


def test_set_seed_repeats_random_sequences() -> None:
    """Seeding twice reproduces each random generator's output."""
    from src.utils import set_seed

    set_seed(42)
    first = (np.random.rand(3), torch.rand(3), random.random())
    set_seed(42)
    second = (np.random.rand(3), torch.rand(3), random.random())

    np.testing.assert_array_equal(first[0], second[0])
    torch.testing.assert_close(first[1], second[1])
    assert first[2] == second[2]
    assert os.environ["PYTHONHASHSEED"] == "42"


def test_get_device_selects_available_device_and_validates_preference() -> None:
    """Device selection works on machines with or without accelerators."""
    from src.utils import get_device

    device = get_device()
    assert isinstance(device, torch.device)
    assert device.type in {"cuda", "mps", "cpu"}
    assert get_device("cpu").type == "cpu"
    with pytest.raises(ValueError):
        get_device("tpu")


def test_json_round_trip_converts_numpy_values(tmp_path) -> None:
    """JSON output preserves the values and creates its parent directory."""
    from src.utils import load_json, save_json

    path = tmp_path / "nested" / "result.json"
    save_json({"count": np.int64(7), "score": np.float32(1.25), "values": np.array([1, 2, 3])}, path)

    assert load_json(path) == {"count": 7, "score": 1.25, "values": [1, 2, 3]}


def test_resolve_path_uses_project_root_only_for_relative_paths(tmp_path) -> None:
    """Relative and absolute paths follow the requested path contract."""
    from src.utils import PROJECT_ROOT, resolve_path

    assert resolve_path("outputs") == PROJECT_ROOT / "outputs"
    assert resolve_path(tmp_path) == tmp_path


def test_ensure_dir_creates_nested_directory(tmp_path) -> None:
    """The directory helper creates and returns the requested path."""
    from src.utils import ensure_dir

    path = tmp_path / "nested" / "folder"
    assert ensure_dir(path) == path
    assert path.is_dir()


def test_load_yaml_reads_mapping_and_empty_file(tmp_path) -> None:
    """YAML mappings load, while an empty file yields an empty dict."""
    from src.utils import load_yaml

    config_path = tmp_path / "config.yaml"
    config_path.write_text("seed: 42\nname: clauses\n", encoding="utf-8")
    empty_path = tmp_path / "empty.yaml"
    empty_path.write_text("", encoding="utf-8")

    assert load_yaml(config_path) == {"seed": 42, "name": "clauses"}
    assert load_yaml(empty_path) == {}


def test_timestamp_uses_log_filename_format() -> None:
    """Timestamps have the expected compact date and time format."""
    from src.utils import timestamp

    assert re.fullmatch(r"\d{8}-\d{6}", timestamp())
