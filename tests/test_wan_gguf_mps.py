from __future__ import annotations

from types import SimpleNamespace

from lpw.generation import wan_gguf_mps


def test_official_block_layout_has_27_tensors() -> None:
    assert len(wan_gguf_mps.BLOCK_TENSOR_SUFFIXES) == 27
    assert wan_gguf_mps.OFFICIAL_S2V_14B["num_layers"] == 40
    assert wan_gguf_mps.OFFICIAL_S2V_14B["dim"] == 5120
    assert wan_gguf_mps.OFFICIAL_S2V_14B["ffn_dim"] == 13824


def test_expected_shapes_match_official_torch_modules() -> None:
    shapes = wan_gguf_mps._expected_block_shapes(wan_gguf_mps.OFFICIAL_S2V_14B)

    assert shapes["self_attn.q.weight"] == (5120, 5120)
    assert shapes["cross_attn.v.weight"] == (5120, 5120)
    assert shapes["ffn.0.weight"] == (13824, 5120)
    assert shapes["ffn.2.weight"] == (5120, 13824)
    assert shapes["modulation"] == (1, 6, 5120)


def test_ggml_dimensions_are_reversed_for_torch() -> None:
    tensor = SimpleNamespace(shape=(5120, 13824))

    assert wan_gguf_mps._tensor_torch_shape(tensor) == (13824, 5120)
