"""Tests for classifier cost and latency helpers."""

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from src.classification.cost import quantize_int8, sample_test, size_on_disk_mb, time_predict


def test_sample_test_selects_seeded_rows_in_original_order(monkeypatch) -> None:
    texts = [f"clause {index}" for index in range(10)]
    labels = np.arange(10)
    monkeypatch.setattr("src.classification.cost.load_split", lambda split: (texts, labels))

    chosen_texts, chosen_labels, indices = sample_test(4)
    expected = np.sort(np.random.default_rng(42).choice(10, 4, replace=False))

    np.testing.assert_array_equal(indices, expected)
    assert chosen_texts == [texts[index] for index in expected]
    np.testing.assert_array_equal(chosen_labels, labels[expected])


def test_time_predict_warms_up_and_reports_median(monkeypatch) -> None:
    class FakeClassifier:
        def __init__(self) -> None:
            self.calls = []

        def predict_proba(self, texts: list[str]) -> np.ndarray:
            self.calls.append(list(texts))
            return np.ones((len(texts), 1), dtype=np.float32)

    clock = iter([0.0, 0.3, 1.0, 1.2, 2.0, 2.4])
    monkeypatch.setattr("src.classification.cost.time.perf_counter", lambda: next(clock))
    classifier = FakeClassifier()

    result = time_predict(classifier, ["a", "b", "c", "d"], repeats=3, warmup=2)

    assert classifier.calls == [["a", "b"]] + [["a", "b", "c", "d"]] * 3
    assert result["n"] == 4
    assert result["repeats"] == 3
    assert result["seconds"] == pytest.approx(0.3)
    assert result["clauses_per_second"] == pytest.approx(4 / 0.3)
    assert result["ms_per_clause"] == pytest.approx(75)
    assert result["seconds_per_1000"] == pytest.approx(75)


def test_size_on_disk_mb_sums_nested_files(tmp_path) -> None:
    model_dir = tmp_path / "model"
    nested = model_dir / "nested"
    nested.mkdir(parents=True)
    (model_dir / "a.bin").write_bytes(b"a" * 1024)
    (nested / "b.bin").write_bytes(b"b" * 2048)

    assert size_on_disk_mb(model_dir) == pytest.approx(3072 / 1024**2)
    assert size_on_disk_mb(model_dir / "a.bin") == pytest.approx(1024 / 1024**2)


def test_quantize_int8_replaces_linear_and_preserves_output() -> None:
    if not hasattr(torch.ao.quantization, "quantize_dynamic"):
        pytest.skip("Dynamic quantization is unavailable in this Torch version")
    torch.manual_seed(42)
    model = torch.nn.Sequential(torch.nn.Linear(4, 8), torch.nn.ReLU(), torch.nn.Linear(8, 2))
    classifier = SimpleNamespace(model=model)
    inputs = torch.randn(5, 4)
    expected = model(inputs).detach().numpy()

    try:
        result = quantize_int8(classifier)
        actual = result.model(inputs).detach().numpy()
    except (AttributeError, NotImplementedError, RuntimeError) as exc:
        pytest.skip(f"Dynamic quantization is unavailable: {exc}")

    assert result is classifier
    assert isinstance(classifier.model[0], torch.ao.nn.quantized.dynamic.Linear)
    assert isinstance(classifier.model[2], torch.ao.nn.quantized.dynamic.Linear)
    np.testing.assert_allclose(actual, expected, rtol=0.15, atol=0.15)
