from __future__ import annotations

from lpw.generation import wan_s2v_transformer


def test_s2v_streaming_constants_match_official_model() -> None:
    assert wan_s2v_transformer.DIM == 5120
    assert wan_s2v_transformer.FFN_DIM == 13824
    assert wan_s2v_transformer.HEADS == 40
    assert wan_s2v_transformer.LAYERS == 40
    assert len(wan_s2v_transformer.AUDIO_INJECT_LAYERS) == 12
