from __future__ import annotations

import numpy as np
import torch

from lpw.generation.wav2vec_s2v import WanAudioEncoder


def test_audio_normalization_is_zero_mean() -> None:
    normalized = WanAudioEncoder._normalize(np.arange(32, dtype=np.float32))

    assert abs(float(normalized.mean())) < 1e-6


def test_audio_bucket_matches_wan_shapes() -> None:
    encoder = object.__new__(WanAudioEncoder)
    encoder.video_rate = 30
    features = torch.ones((25, 150, 1024), dtype=torch.float16)

    bucket, repeats = encoder.bucket(features, fps=16, frames=80)

    assert repeats == 2
    assert bucket.shape == (160, 25, 1024)
