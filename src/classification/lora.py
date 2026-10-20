"""Low-rank linear adapters following TP06 Part C."""

import torch
from torch import nn


class LoRALinear(nn.Module):
    """Apply a frozen linear layer plus a scaled rank-r update."""

    def __init__(self, base: nn.Linear, r: int = 8, alpha: int = 16) -> None:
        """Freeze the base and initialize A randomly and B to zero."""
        super().__init__()
        if r <= 0:
            raise ValueError("r must be positive")
        self.base = base
        for parameter in self.base.parameters():
            parameter.requires_grad = False
        self.A = nn.Parameter(
            torch.randn(r, base.in_features, device=base.weight.device, dtype=base.weight.dtype) * 0.01
        )
        self.B = nn.Parameter(torch.zeros(base.out_features, r, device=base.weight.device, dtype=base.weight.dtype))
        self.scaling = alpha / r

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add the low-rank update to the frozen base output."""
        return self.base(x) + self.scaling * (x @ self.A.T @ self.B.T)


def inject_lora(
    model: nn.Module, targets: tuple[str, ...] = ("query", "value"), r: int = 8,
    alpha: int = 16, head: tuple[str, ...] = ("classifier",),
) -> nn.Module:
    """Replace named linear projections and unfreeze adapter and head weights."""
    for parameter in model.parameters():
        parameter.requires_grad = False
    for module in list(model.modules()):
        for name, child in list(module.named_children()):
            if name in targets and isinstance(child, nn.Linear):
                setattr(module, name, LoRALinear(child, r=r, alpha=alpha))
    for name, module in model.named_children():
        if name in head:
            for parameter in module.parameters():
                parameter.requires_grad = True
    return model


def merge_lora(layer: LoRALinear) -> nn.Linear:
    """Fold an adapter into a plain linear layer with the original bias."""
    base = layer.base
    merged = nn.Linear(base.in_features, base.out_features, bias=base.bias is not None,
                       device=base.weight.device, dtype=base.weight.dtype)
    with torch.no_grad():
        merged.weight.copy_(base.weight + layer.scaling * (layer.B @ layer.A))
        if base.bias is not None:
            merged.bias.copy_(base.bias)
    return merged


def merge_all_lora(model: nn.Module) -> nn.Module:
    """Replace every adapter in a model with its merged linear layer."""
    for module in list(model.modules()):
        for name, child in list(module.named_children()):
            if isinstance(child, LoRALinear):
                setattr(module, name, merge_lora(child))
    return model


def count_parameters(model: nn.Module) -> tuple[int, int]:
    """Return trainable and total parameter counts."""
    parameters = list(model.parameters())
    return sum(p.numel() for p in parameters if p.requires_grad), sum(p.numel() for p in parameters)


def training_memory_gb(n_frozen: int, n_trained: int, bytes_frozen: int = 4) -> float:
    """Estimate weight, gradient, and Adam state memory in decimal GB."""
    return (n_frozen * bytes_frozen + n_trained * 16) / 1e9
