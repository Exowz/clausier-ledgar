"""Offline tests for hand-written LoRA."""

import numpy as np
import torch
from torch import nn
from transformers import AutoModelForSequenceClassification

from src.classification.lora import (
    LoRALinear,
    count_parameters,
    inject_lora,
    merge_all_lora,
    merge_lora,
    training_memory_gb,
)
from src.classification.train import DEFAULTS, run_training

pytest_plugins = ("tests.test_train",)


def test_lora_initialization_and_gradient():
    torch.manual_seed(42)
    base = nn.Linear(768, 768)
    layer = LoRALinear(base, r=8, alpha=16)
    x = torch.randn(2, 768)
    torch.testing.assert_close(layer(x), base(x))
    assert count_parameters(layer)[0] == 12_288
    assert not base.weight.requires_grad
    layer(x).sum().backward()
    assert layer.B.grad is not None and layer.B.grad.abs().sum() > 0
    assert base.weight.grad is None


def test_merge_lora_preserves_output_and_rank():
    layer = LoRALinear(nn.Linear(16, 12), r=3, alpha=6)
    with torch.no_grad():
        layer.B.normal_()
    x = torch.randn(4, 16)
    merged = merge_lora(layer)
    torch.testing.assert_close(merged(x), layer(x), atol=1e-5, rtol=1e-5)
    assert torch.linalg.matrix_rank(merged.weight - layer.base.weight) <= 3
    assert training_memory_gb(0, 110_000_000) == 1.76


def test_inject_and_merge_tiny_bert(tiny_model_dir):
    model = AutoModelForSequenceClassification.from_pretrained(tiny_model_dir)
    model.eval()
    inputs = {"input_ids": torch.tensor([[2, 5, 3]])}
    original = model(**inputs).logits.detach()
    inject_lora(model)
    assert sum(isinstance(module, LoRALinear) for module in model.modules()) == 4
    assert all(".A" in name or ".B" in name or name.startswith("classifier.")
               for name, parameter in model.named_parameters() if parameter.requires_grad)
    torch.testing.assert_close(model(**inputs).logits, original)
    merge_all_lora(model)
    assert not any(isinstance(module, LoRALinear) for module in model.modules())
    torch.testing.assert_close(model(**inputs).logits, original, atol=1e-5, rtol=1e-5)


def test_lora_training_saves_plain_bert(tiny_model_dir, tiny_data, tmp_path):
    config = {**DEFAULTS, "model_name": str(tiny_model_dir), "run_name": "tiny_lora", "device": "cpu",
              "use_lora": True, "epochs": 1, "batch_size": 8, "eval_batch_size": 8, "max_length": 16,
              "num_workers": 0}
    run_training(config, tiny_data, ["apple", "ocean", "rocket", "forest"], tmp_path)
    model = AutoModelForSequenceClassification.from_pretrained(tmp_path / "tiny_lora" / "model")
    assert not any(isinstance(module, LoRALinear) for module in model.modules())
    assert np.load(tmp_path / "tiny_lora" / "test_probs.npy").shape == (12, 4)
