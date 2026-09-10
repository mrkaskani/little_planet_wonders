from __future__ import annotations

import torch

from lpw.generation.wan_vae import VAE_MEAN, VAE_STD


def test_vae_scale_has_all_latent_channels() -> None:
    assert len(VAE_MEAN) == 16
    assert len(VAE_STD) == 16
    assert torch.tensor(VAE_STD).gt(0).all()
