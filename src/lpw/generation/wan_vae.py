"""Wan 2.1 VAE loading and normalization for the local S2V backend."""

from __future__ import annotations

import gc
from pathlib import Path
from typing import Any


VAE_MEAN = (
    -0.7571, -0.7089, -0.9113, 0.1075, -0.1745, 0.9653, -0.1517, 1.5508,
    0.4134, -0.0715, 0.5517, -0.3632, -0.1922, -0.9497, 0.2503, -0.2921,
)
VAE_STD = (
    2.8184, 1.4541, 2.3275, 2.6558, 1.2196, 1.7708, 2.6052, 2.0743,
    3.2687, 2.1526, 2.8652, 1.5579, 1.6382, 1.1253, 2.8251, 1.9160,
)


def _middle_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    residual_parts = {
        "residual.0.gamma": "norm1.gamma",
        "residual.2.bias": "conv1.bias",
        "residual.2.weight": "conv1.weight",
        "residual.3.gamma": "norm2.gamma",
        "residual.6.bias": "conv2.bias",
        "residual.6.weight": "conv2.weight",
    }
    for side in ("encoder", "decoder"):
        for old_index, new_index in ((0, 0), (2, 1)):
            for old_suffix, new_suffix in residual_parts.items():
                mapping[f"{side}.middle.{old_index}.{old_suffix}"] = (
                    f"{side}.mid_block.resnets.{new_index}.{new_suffix}"
                )
        for suffix in ("norm.gamma", "to_qkv.weight", "to_qkv.bias", "proj.weight", "proj.bias"):
            mapping[f"{side}.middle.1.{suffix}"] = f"{side}.mid_block.attentions.0.{suffix}"
    return mapping


def convert_wan_vae_state_dict(original: dict[str, Any]) -> dict[str, Any]:
    """Apply Hugging Face's official Wan 2.1 VAE key conversion."""
    direct = _middle_mapping()
    direct.update(
        {
            "encoder.head.0.gamma": "encoder.norm_out.gamma",
            "encoder.head.2.bias": "encoder.conv_out.bias",
            "encoder.head.2.weight": "encoder.conv_out.weight",
            "decoder.head.0.gamma": "decoder.norm_out.gamma",
            "decoder.head.2.bias": "decoder.conv_out.bias",
            "decoder.head.2.weight": "decoder.conv_out.weight",
            "conv1.weight": "quant_conv.weight",
            "conv1.bias": "quant_conv.bias",
            "conv2.weight": "post_quant_conv.weight",
            "conv2.bias": "post_quant_conv.bias",
            "encoder.conv1.weight": "encoder.conv_in.weight",
            "encoder.conv1.bias": "encoder.conv_in.bias",
            "decoder.conv1.weight": "decoder.conv_in.weight",
            "decoder.conv1.bias": "decoder.conv_in.bias",
        }
    )
    converted: dict[str, Any] = {}
    for key, value in original.items():
        if key in direct:
            converted[direct[key]] = value
            continue
        if key.startswith("encoder.downsamples."):
            new_key = key.replace("encoder.downsamples.", "encoder.down_blocks.")
            replacements = (
                (".residual.0.gamma", ".norm1.gamma"),
                (".residual.2.bias", ".conv1.bias"),
                (".residual.2.weight", ".conv1.weight"),
                (".residual.3.gamma", ".norm2.gamma"),
                (".residual.6.bias", ".conv2.bias"),
                (".residual.6.weight", ".conv2.weight"),
                (".shortcut.bias", ".conv_shortcut.bias"),
                (".shortcut.weight", ".conv_shortcut.weight"),
            )
            for old, new in replacements:
                if old in new_key:
                    new_key = new_key.replace(old, new)
                    break
            converted[new_key] = value
            continue
        if key.startswith("decoder.upsamples."):
            block_index = int(key.split(".")[2])
            if "residual" in key:
                groups = {0: (0, 0), 1: (0, 1), 2: (0, 2), 4: (1, 0), 5: (1, 1), 6: (1, 2),
                          8: (2, 0), 9: (2, 1), 10: (2, 2), 12: (3, 0), 13: (3, 1), 14: (3, 2)}
                group, resnet = groups[block_index]
                suffixes = {
                    ".residual.0.gamma": "norm1.gamma",
                    ".residual.2.bias": "conv1.bias",
                    ".residual.2.weight": "conv1.weight",
                    ".residual.3.gamma": "norm2.gamma",
                    ".residual.6.bias": "conv2.bias",
                    ".residual.6.weight": "conv2.weight",
                }
                suffix = next(new for old, new in suffixes.items() if old in key)
                converted[f"decoder.up_blocks.{group}.resnets.{resnet}.{suffix}"] = value
            elif ".shortcut." in key:
                if block_index == 4:
                    new_key = key.replace("decoder.upsamples.4", "decoder.up_blocks.1")
                    new_key = new_key.replace(".shortcut.", ".resnets.0.conv_shortcut.")
                else:
                    new_key = key.replace("decoder.upsamples.", "decoder.up_blocks.")
                    new_key = new_key.replace(".shortcut.", ".conv_shortcut.")
                converted[new_key] = value
            elif ".resample." in key or ".time_conv." in key:
                upsampler_groups = {3: 0, 7: 1, 11: 2}
                if block_index in upsampler_groups:
                    new_key = key.replace(
                        f"decoder.upsamples.{block_index}",
                        f"decoder.up_blocks.{upsampler_groups[block_index]}.upsamplers.0",
                    )
                else:
                    new_key = key.replace("decoder.upsamples.", "decoder.up_blocks.")
                converted[new_key] = value
            else:
                converted[key.replace("decoder.upsamples.", "decoder.up_blocks.")] = value
            continue
        converted[key] = value
    return converted


class WanVAE:
    """Strictly load the converted BF16 VAE and offload it between phases."""

    def __init__(self, checkpoint: str | Path, device: str = "mps") -> None:
        import torch
        from diffusers import AutoencoderKLWan
        from safetensors.torch import load_file

        self.checkpoint = Path(checkpoint).expanduser().resolve()
        self.device = torch.device(device)
        original = load_file(str(self.checkpoint), device="cpu")
        converted = convert_wan_vae_state_dict(original)
        with torch.device("meta"):
            model = AutoencoderKLWan()
        model.load_state_dict(converted, strict=True, assign=True)
        model.enable_tiling(
            tile_sample_min_height=128,
            tile_sample_min_width=128,
            tile_sample_stride_height=96,
            tile_sample_stride_width=96,
        )
        self.model = model.eval().requires_grad_(False)
        self.dtype = next(model.parameters()).dtype
        del original, converted

    def _scale(self, device: Any, dtype: Any) -> tuple[Any, Any]:
        import torch

        mean = torch.tensor(VAE_MEAN, device=device, dtype=dtype).view(1, 16, 1, 1, 1)
        inverse_std = torch.tensor(VAE_STD, device=device, dtype=dtype).reciprocal().view(1, 16, 1, 1, 1)
        return mean, inverse_std

    def encode(self, pixels: Any) -> Any:
        import torch

        self.model.to(self.device)
        pixels = pixels.to(device=self.device, dtype=self.dtype)
        with torch.inference_mode():
            latent = self.model.encode(pixels).latent_dist.mode()
            mean, inverse_std = self._scale(latent.device, latent.dtype)
            latent = ((latent - mean) * inverse_std).to("cpu")
        self.model.to("cpu")
        del pixels, mean, inverse_std
        gc.collect()
        torch.mps.empty_cache()
        torch.mps.synchronize()
        return latent

    def decode(self, latent: Any, emit: Any | None = None, job_id: str | None = None) -> Any:
        """Decode video latents with per-tile CPU offload.

        Args:
            latent: Normalized Wan video latents in CPU memory.
            emit: Optional structured progress callback.
            job_id: Active job identifier for progress events.

        Returns:
            Decoded pixels in CPU memory with values in the range ``[-1, 1]``.
        """
        import torch

        self.model.to(self.device)
        latent = latent.to(device="cpu", dtype=self.dtype)
        mean, inverse_std = self._scale(latent.device, latent.dtype)
        latent = latent / inverse_std + mean
        with torch.inference_mode():
            pixels = self._decode_cpu_offloaded_tiles(latent, emit=emit, job_id=job_id)
        self.model.to("cpu")
        del latent, mean, inverse_std
        gc.collect()
        torch.mps.empty_cache()
        torch.mps.synchronize()
        return pixels

    def _decode_cpu_offloaded_tiles(
        self, latent: Any, emit: Any | None = None, job_id: str | None = None
    ) -> Any:
        """Decode smaller spatial tiles and offload every temporal result.

        Args:
            latent: Unscaled BF16 latent tensor resident on CPU.
            emit: Optional structured progress callback.
            job_id: Active job identifier for progress events.

        Returns:
            A stitched CPU float32 video tensor.
        """
        import torch

        model = self.model
        _, _, num_frames, height, width = latent.shape
        ratio = model.spatial_compression_ratio
        tile_height = model.tile_sample_min_height // ratio
        tile_width = model.tile_sample_min_width // ratio
        stride_height = model.tile_sample_stride_height // ratio
        stride_width = model.tile_sample_stride_width // ratio
        sample_stride_height = model.tile_sample_stride_height
        sample_stride_width = model.tile_sample_stride_width
        sample_height = height * ratio
        sample_width = width * ratio
        blend_height = model.tile_sample_min_height - sample_stride_height
        blend_width = model.tile_sample_min_width - sample_stride_width
        if model.config.patch_size is not None:
            patch_size = model.config.patch_size
            sample_height //= patch_size
            sample_width //= patch_size
            sample_stride_height //= patch_size
            sample_stride_width //= patch_size
            blend_height = model.tile_sample_min_height // patch_size - sample_stride_height
            blend_width = model.tile_sample_min_width // patch_size - sample_stride_width

        row_offsets = list(range(0, height, stride_height))
        column_offsets = list(range(0, width, stride_width))
        total_tiles = len(row_offsets) * len(column_offsets)
        completed_tiles = 0
        rows = []
        for top in row_offsets:
            row = []
            for left in column_offsets:
                model.clear_cache()
                temporal_parts = []
                for frame_index in range(num_frames):
                    model._conv_idx = [0]
                    tile = latent[
                        :, :, frame_index : frame_index + 1,
                        top : top + tile_height,
                        left : left + tile_width,
                    ].to(self.device)
                    projected = model.post_quant_conv(tile)
                    decoded = model.decoder(
                        projected,
                        feat_cache=model._feat_map,
                        feat_idx=model._conv_idx,
                        first_chunk=(frame_index == 0),
                    )
                    temporal_parts.append(decoded.to("cpu"))
                    del tile, projected, decoded
                    torch.mps.synchronize()
                    torch.mps.empty_cache()
                row.append(torch.cat(temporal_parts, dim=2))
                del temporal_parts
                model.clear_cache()
                torch.mps.empty_cache()
                torch.mps.synchronize()
                completed_tiles += 1
                if emit is not None:
                    emit(
                        "running", "vae-tile",
                        f"decoded CPU-offloaded VAE tile {completed_tiles}/{total_tiles}",
                        job_id=job_id,
                        completed_tiles=completed_tiles,
                        total_tiles=total_tiles,
                    )
            rows.append(row)

        result_rows = []
        for row_index, row in enumerate(rows):
            result_row = []
            for column_index, tile in enumerate(row):
                if row_index > 0:
                    tile = model.blend_v(rows[row_index - 1][column_index], tile, blend_height)
                if column_index > 0:
                    tile = model.blend_h(row[column_index - 1], tile, blend_width)
                result_row.append(
                    tile[:, :, :, :sample_stride_height, :sample_stride_width]
                )
            result_rows.append(torch.cat(result_row, dim=-1))
        pixels = torch.cat(result_rows, dim=3)[:, :, :, :sample_height, :sample_width]
        if model.config.patch_size is not None:
            from diffusers.models.autoencoders.autoencoder_kl_wan import unpatchify

            pixels = unpatchify(pixels, patch_size=model.config.patch_size)
        model.clear_cache()
        return pixels.float().clamp_(-1, 1)


def load_reference_pixels(path: str | Path, width: int, height: int) -> Any:
    import numpy as np
    import torch
    from PIL import Image

    image = Image.open(path).convert("RGB")
    if image.size != (width, height):
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    array = np.asarray(image, dtype=np.float32) / 127.5 - 1.0
    return torch.from_numpy(array).permute(2, 0, 1).unsqueeze(0).unsqueeze(2)
