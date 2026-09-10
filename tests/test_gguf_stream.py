from __future__ import annotations

from lpw.generation.umt5_gguf_mps import UMT5GGUFEncoder


def test_umt5_gated_gelu_is_finite() -> None:
    import torch

    result = UMT5GGUFEncoder._gated_gelu(torch.tensor([-2.0, 0.0, 2.0]))

    assert torch.isfinite(result).all()
    assert result[1].item() == 0.0
