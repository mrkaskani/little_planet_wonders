"""Layer-streamed Wan 2.2 S2V transformer execution on Apple MPS."""

from __future__ import annotations

import gc
import math
from pathlib import Path
from typing import Any

from .gguf_stream import GGUFStore


DIM = 5120
FFN_DIM = 13824
HEADS = 40
HEAD_DIM = 128
LAYERS = 40
PATCH = (1, 2, 2)
AUDIO_INJECT_LAYERS = (0, 4, 8, 12, 16, 20, 24, 27, 30, 33, 36, 39)


class WanS2VStreamedTransformer:
    """Execute S2V-14B while retaining at most one transformer block."""

    def __init__(self, gguf_path: str | Path, device: str = "mps") -> None:
        import torch

        self.store = GGUFStore(gguf_path)
        self.device = torch.device(device)
        self.dtype = torch.bfloat16
        self.eps = 1e-6
        self._validate()

    def _validate(self) -> None:
        for block in range(LAYERS):
            if len(self.store.names(f"blocks.{block}.")) != 27:
                raise RuntimeError(f"Wan S2V block {block} does not contain 27 tensors")
        if len(self.store.names("audio_injector.injector.")) != 120:
            raise RuntimeError("Wan S2V checkpoint does not contain 12 audio cross-attention modules")

    def _weight(self, name: str, *, fp32: bool = False) -> Any:
        import torch

        return self.store.tensor(
            name,
            device=str(self.device),
            dtype=torch.float32 if fp32 else self.dtype,
        )

    @staticmethod
    def _linear(x: Any, weight: Any, bias: Any | None = None) -> Any:
        import torch.nn.functional as functional

        return functional.linear(x, weight, bias)

    def _layer_norm(self, x: Any, weight: Any | None = None, bias: Any | None = None) -> Any:
        import torch.nn.functional as functional

        normalized = functional.layer_norm(
            x.float(), (DIM,),
            None if weight is None else weight.float(),
            None if bias is None else bias.float(),
            self.eps,
        )
        return normalized.to(self.dtype)

    def _rms_norm(self, x: Any, weight: Any) -> Any:
        import torch

        normalized = x.float() * torch.rsqrt(x.float().pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return normalized.to(self.dtype) * weight

    @staticmethod
    def _sinusoidal_embedding(timestep: Any, dim: int = 256) -> Any:
        import torch

        half = dim // 2
        target_device = timestep.device
        # MPS has no float64 support. The official formula only needs float64
        # for this tiny scalar embedding, so calculate it on CPU exactly.
        position = timestep.to(device="cpu", dtype=torch.float64)
        frequencies = torch.pow(
            10000,
            -torch.arange(half, device="cpu", dtype=torch.float64) / half,
        )
        values = torch.outer(position, frequencies)
        return torch.cat([torch.cos(values), torch.sin(values)], dim=1).float().to(target_device)

    @staticmethod
    def _axis_angles(positions: Any, pair_count: int) -> Any:
        import torch

        exponents = torch.arange(pair_count, device=positions.device, dtype=torch.float32) / pair_count
        inverse = torch.pow(torch.tensor(10000.0, device=positions.device), -exponents)
        return positions.float().unsqueeze(1) * inverse.unsqueeze(0)

    def _rope_for_grid(
        self,
        frames: Any,
        heights: Any,
        widths: Any,
    ) -> tuple[Any, Any]:
        import torch

        frame_angles = self._axis_angles(frames, 22)
        height_angles = self._axis_angles(heights, 21)
        width_angles = self._axis_angles(widths, 21)
        f, h, w = len(frames), len(heights), len(widths)
        angles = torch.cat(
            [
                frame_angles[:, None, None, :].expand(f, h, w, 22),
                height_angles[None, :, None, :].expand(f, h, w, 21),
                width_angles[None, None, :, :].expand(f, h, w, 21),
            ],
            dim=-1,
        ).reshape(f * h * w, 64)
        return angles.cos().to(self.dtype), angles.sin().to(self.dtype)

    def _standard_rope(self, frames: int, height: int, width: int, start_frame: int = 0) -> tuple[Any, Any]:
        import torch

        return self._rope_for_grid(
            torch.arange(start_frame, start_frame + frames, device=self.device),
            torch.arange(height, device=self.device),
            torch.arange(width, device=self.device),
        )

    @staticmethod
    def _apply_rope(x: Any, cos: Any, sin: Any) -> Any:
        pairs = x.reshape(*x.shape[:-1], 64, 2)
        first, second = pairs[..., 0], pairs[..., 1]
        cos = cos.unsqueeze(0).unsqueeze(2)
        sin = sin.unsqueeze(0).unsqueeze(2)
        rotated = __import__("torch").stack(
            (first * cos - second * sin, first * sin + second * cos), dim=-1
        )
        return rotated.flatten(-2)

    def _load_block(self, index: int) -> dict[str, Any]:
        prefix = f"blocks.{index}."
        weights = {}
        for name in self.store.names(prefix):
            suffix = name[len(prefix):]
            weights[suffix] = self._weight(name, fp32=suffix == "modulation")
        return weights

    def _attention(
        self,
        x: Any,
        weights: dict[str, Any],
        prefix: str,
        context: Any | None = None,
        rope: tuple[Any, Any] | None = None,
    ) -> Any:
        import torch.nn.functional as functional

        source = x if context is None else context
        q = self._linear(x, weights[f"{prefix}.q.weight"], weights[f"{prefix}.q.bias"])
        k = self._linear(source, weights[f"{prefix}.k.weight"], weights[f"{prefix}.k.bias"])
        v = self._linear(source, weights[f"{prefix}.v.weight"], weights[f"{prefix}.v.bias"])
        q = self._rms_norm(q, weights[f"{prefix}.norm_q.weight"])
        k = self._rms_norm(k, weights[f"{prefix}.norm_k.weight"])
        q = q.view(q.shape[0], q.shape[1], HEADS, HEAD_DIM)
        k = k.view(k.shape[0], k.shape[1], HEADS, HEAD_DIM)
        v = v.view(v.shape[0], v.shape[1], HEADS, HEAD_DIM)
        if rope is not None:
            q = self._apply_rope(q, *rope)
            k = self._apply_rope(k, *rope)
        attended = functional.scaled_dot_product_attention(
            q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)
        )
        attended = attended.transpose(1, 2).reshape(x.shape[0], x.shape[1], DIM)
        return self._linear(attended, weights[f"{prefix}.o.weight"], weights[f"{prefix}.o.bias"])

    @staticmethod
    def _segment_modulation(x: Any, values: Any, split: int) -> Any:
        first = x[:, :split] * (1 + values[:, 0:1])
        second = x[:, split:] * (1 + values[:, 1:2])
        return __import__("torch").cat([first, second], dim=1)

    @staticmethod
    def _segment_shift(x: Any, values: Any, split: int) -> Any:
        first = x[:, :split] + values[:, 0:1]
        second = x[:, split:] + values[:, 1:2]
        return __import__("torch").cat([first, second], dim=1)

    @staticmethod
    def _segment_scale(x: Any, values: Any, split: int) -> Any:
        first = x[:, :split] * values[:, 0:1]
        second = x[:, split:] * values[:, 1:2]
        return __import__("torch").cat([first, second], dim=1)

    def _block(self, x: Any, context: Any, e0: Any, split: int, rope: tuple[Any, Any], weights: dict[str, Any]) -> Any:
        import torch
        import torch.nn.functional as functional

        modulation = weights["modulation"].unsqueeze(2)
        values = [(part.squeeze(1)) for part in (modulation + e0).chunk(6, dim=1)]
        normalized = self._layer_norm(x).float()
        normalized = self._segment_shift(
            self._segment_modulation(normalized, values[1], split), values[0], split
        ).to(self.dtype)
        attended = self._attention(normalized, weights, "self_attn", rope=rope)
        x = x + self._segment_scale(attended.float(), values[2], split).to(self.dtype)

        normalized = self._layer_norm(
            x, weights["norm3.weight"], weights["norm3.bias"]
        )
        x = x + self._attention(normalized, weights, "cross_attn", context=context)
        normalized = self._layer_norm(x).float()
        normalized = self._segment_shift(
            self._segment_modulation(normalized, values[4], split), values[3], split
        ).to(self.dtype)
        hidden = self._linear(normalized, weights["ffn.0.weight"], weights["ffn.0.bias"])
        hidden = functional.gelu(hidden, approximate="tanh")
        hidden = self._linear(hidden, weights["ffn.2.weight"], weights["ffn.2.bias"])
        x = x + self._segment_scale(hidden.float(), values[5], split).to(self.dtype)
        return x

    def _release(self, *values: Any) -> None:
        import torch

        del values
        gc.collect()
        torch.mps.empty_cache()
        torch.mps.synchronize()

    def _causal_conv1d(self, x: Any, weight: Any, bias: Any, stride: int = 1) -> Any:
        import torch.nn.functional as functional

        x = functional.pad(x, (2, 0), mode="replicate")
        return functional.conv1d(x, weight, bias, stride=stride)

    def prepare_audio_embeddings(
        self,
        audio_input: Any,
        motion_frames: int = 73,
        latent_motion_frames: int = 19,
    ) -> tuple[Any, Any]:
        """Run the checkpoint's causal audio encoder and retain target frames."""
        import torch
        import torch.nn.functional as functional

        audio_input = audio_input.to(device=self.device, dtype=self.dtype)
        audio_input = torch.cat(
            [audio_input[..., :1].repeat(1, 1, 1, motion_frames), audio_input], dim=-1
        )
        names = self.store.names("casual_audio_encoder.")
        weights = {name.removeprefix("casual_audio_encoder."): self._weight(name) for name in names}
        mixing = functional.silu(weights["weights"])
        mixed = ((audio_input * mixing) / mixing.sum(dim=1, keepdim=True)).sum(dim=1)

        local = self._causal_conv1d(
            mixed,
            weights["encoder.conv1_local.conv.weight"],
            weights["encoder.conv1_local.conv.bias"],
        )
        batch, _, frames = local.shape
        local = local.view(batch, 4, 1280, frames).permute(0, 1, 3, 2).reshape(batch * 4, frames, 1280)
        local = functional.layer_norm(local.float(), (1280,), eps=self.eps).to(self.dtype)
        local = functional.silu(local).transpose(1, 2)
        local = self._causal_conv1d(
            local, weights["encoder.conv2.conv.weight"], weights["encoder.conv2.conv.bias"], stride=2
        ).transpose(1, 2)
        local = functional.silu(
            functional.layer_norm(local.float(), (2560,), eps=self.eps).to(self.dtype)
        ).transpose(1, 2)
        local = self._causal_conv1d(
            local, weights["encoder.conv3.conv.weight"], weights["encoder.conv3.conv.bias"], stride=2
        ).transpose(1, 2)
        local = functional.silu(
            functional.layer_norm(local.float(), (DIM,), eps=self.eps).to(self.dtype)
        )
        local = local.view(batch, 4, local.shape[1], DIM).permute(0, 2, 1, 3)
        padding = weights["encoder.padding_tokens"].expand(batch, local.shape[1], 1, DIM)
        local = torch.cat([local, padding], dim=2)

        global_audio = self._causal_conv1d(
            mixed,
            weights["encoder.conv1_global.conv.weight"],
            weights["encoder.conv1_global.conv.bias"],
        ).transpose(1, 2)
        global_audio = functional.silu(
            functional.layer_norm(global_audio.float(), (1280,), eps=self.eps).to(self.dtype)
        ).transpose(1, 2)
        global_audio = self._causal_conv1d(
            global_audio,
            weights["encoder.conv2.conv.weight"],
            weights["encoder.conv2.conv.bias"],
            stride=2,
        ).transpose(1, 2)
        global_audio = functional.silu(
            functional.layer_norm(global_audio.float(), (2560,), eps=self.eps).to(self.dtype)
        ).transpose(1, 2)
        global_audio = self._causal_conv1d(
            global_audio,
            weights["encoder.conv3.conv.weight"],
            weights["encoder.conv3.conv.bias"],
            stride=2,
        ).transpose(1, 2)
        global_audio = functional.silu(
            functional.layer_norm(global_audio.float(), (DIM,), eps=self.eps).to(self.dtype)
        )
        global_audio = self._linear(
            global_audio,
            weights["encoder.final_linear.weight"],
            weights["encoder.final_linear.bias"],
        ).unsqueeze(2)
        local = local[:, latent_motion_frames:].contiguous()
        global_audio = global_audio[:, latent_motion_frames:].contiguous()
        del weights, mixed, mixing, audio_input
        self._release()
        return global_audio, local

    def _audio_inject(
        self,
        x: Any,
        original_grid: tuple[int, int, int],
        global_audio: Any,
        local_audio: Any,
        injector_index: int,
    ) -> Any:
        import torch
        import torch.nn.functional as functional

        frames, height, width = original_grid
        spatial = height * width
        original_length = frames * spatial
        hidden = x[:, :original_length].reshape(1, frames, spatial, DIM).reshape(frames, spatial, DIM)
        prefix = f"audio_injector.injector.{injector_index}."
        attention = {
            name[len(prefix):]: self._weight(name) for name in self.store.names(prefix)
        }
        adain_prefix = f"audio_injector.injector_adain_layers.{injector_index}.linear."
        adain_weight = self._weight(adain_prefix + "weight")
        adain_bias = self._weight(adain_prefix + "bias")
        temporal = global_audio.reshape(frames, DIM)
        shift, scale = self._linear(functional.silu(temporal), adain_weight, adain_bias).chunk(2, dim=1)
        normalized = functional.layer_norm(hidden.float(), (DIM,), eps=self.eps).to(self.dtype)
        normalized = normalized * (1 + scale[:, None]) + shift[:, None]

        audio_context = local_audio.reshape(frames, local_audio.shape[2], DIM)
        q = self._rms_norm(
            self._linear(normalized, attention["q.weight"], attention["q.bias"]),
            attention["norm_q.weight"],
        )
        k = self._rms_norm(
            self._linear(audio_context, attention["k.weight"], attention["k.bias"]),
            attention["norm_k.weight"],
        )
        v = self._linear(audio_context, attention["v.weight"], attention["v.bias"])
        q = q.view(frames, spatial, HEADS, HEAD_DIM).transpose(1, 2)
        k = k.view(frames, -1, HEADS, HEAD_DIM).transpose(1, 2)
        v = v.view(frames, -1, HEADS, HEAD_DIM).transpose(1, 2)
        residual = functional.scaled_dot_product_attention(q, k, v)
        residual = residual.transpose(1, 2).reshape(frames, spatial, DIM)
        residual = self._linear(residual, attention["o.weight"], attention["o.bias"])
        x[:, :original_length] += residual.reshape(1, original_length, DIM)
        del attention, adain_weight, adain_bias, hidden, normalized, temporal, shift, scale
        del audio_context, q, k, v, residual
        self._release()
        return x

    def _framepack(
        self, motion_latents: Any, add_last_motion: int = 2
    ) -> tuple[Any, tuple[Any, Any]]:
        import numpy as np
        import torch
        import torch.nn.functional as functional

        names = self.store.names("frame_packer.")
        weights = {name.removeprefix("frame_packer."): self._weight(name) for name in names}
        batch, channels, _, latent_height, latent_width = motion_latents.shape
        padded = torch.zeros(
            (batch, channels, 19, latent_height, latent_width),
            device=self.device,
            dtype=self.dtype,
        )
        overlap = min(19, motion_latents.shape[2])
        padded[:, :, -overlap:] = motion_latents[:, :, -overlap:]
        far, middle, near = padded.split((16, 2, 1), dim=2)
        if add_last_motion < 2:
            near.zero_()
        if add_last_motion < 1:
            middle.zero_()
        near = functional.conv3d(
            near, weights["proj.weight"], weights["proj.bias"], stride=(1, 2, 2)
        ).flatten(2).transpose(1, 2)
        middle = functional.conv3d(
            middle, weights["proj_2x.weight"], weights["proj_2x.bias"], stride=(2, 4, 4)
        ).flatten(2).transpose(1, 2)
        far = functional.conv3d(
            far, weights["proj_4x.weight"], weights["proj_4x.bias"], stride=(4, 8, 8)
        ).flatten(2).transpose(1, 2)
        tokens = torch.cat([near, middle, far], dim=1)

        def sampled_positions(start: int, total: int, count: int) -> Any:
            if start >= 0:
                values = np.linspace(start, total + start - 1, count).astype(int)
            else:
                values = -np.linspace(-start, (-total - start) + 1, count).astype(int)
            return torch.tensor(values, device=self.device)

        near_rope = self._rope_for_grid(
            sampled_positions(-1, 1, near.shape[1] // ((latent_height // 2) * (latent_width // 2))),
            sampled_positions(0, latent_height // 2, latent_height // 2),
            sampled_positions(0, latent_width // 2, latent_width // 2),
        )
        middle_rope = self._rope_for_grid(
            sampled_positions(-3, 2, 1),
            sampled_positions(0, latent_height // 2, latent_height // 4),
            sampled_positions(0, latent_width // 2, latent_width // 4),
        )
        far_rope = self._rope_for_grid(
            sampled_positions(-19, 16, 4),
            sampled_positions(0, latent_height // 2, latent_height // 8),
            sampled_positions(0, latent_width // 2, latent_width // 8),
        )
        rope = (
            torch.cat([near_rope[0], middle_rope[0], far_rope[0]], dim=0),
            torch.cat([near_rope[1], middle_rope[1], far_rope[1]], dim=0),
        )
        del weights, padded, near, middle, far
        self._release()
        return tokens, rope

    def prepare_tokens(
        self,
        noisy_latents: Any,
        reference_latents: Any,
        condition_latents: Any,
        motion_latents: Any,
        *,
        drop_motion: bool,
    ) -> tuple[Any, tuple[Any, Any], tuple[int, int, int], int]:
        import torch
        import torch.nn.functional as functional

        globals_to_load = (
            "patch_embedding.weight", "patch_embedding.bias",
            "cond_encoder.weight", "cond_encoder.bias",
            "trainable_cond_mask.weight",
        )
        weights = {name: self._weight(name) for name in globals_to_load}
        target = functional.conv3d(
            noisy_latents.to(self.device, self.dtype),
            weights["patch_embedding.weight"], weights["patch_embedding.bias"], stride=PATCH,
        )
        condition = functional.conv3d(
            condition_latents.to(self.device, self.dtype),
            weights["cond_encoder.weight"], weights["cond_encoder.bias"], stride=PATCH,
        )
        target = target + condition
        grid = (target.shape[2], target.shape[3], target.shape[4])
        target = target.flatten(2).transpose(1, 2)
        original_length = target.shape[1]
        reference = functional.conv3d(
            reference_latents.to(self.device, self.dtype),
            weights["patch_embedding.weight"], weights["patch_embedding.bias"], stride=PATCH,
        ).flatten(2).transpose(1, 2)
        tokens = torch.cat([target, reference], dim=1)
        mask = torch.cat(
            [torch.zeros(original_length, device=self.device, dtype=torch.long),
             torch.ones(reference.shape[1], device=self.device, dtype=torch.long)]
        )
        target_rope = self._standard_rope(*grid)
        reference_rope = self._standard_rope(1, grid[1], grid[2], start_frame=30)
        rope = (
            torch.cat([target_rope[0], reference_rope[0]], dim=0),
            torch.cat([target_rope[1], reference_rope[1]], dim=0),
        )
        if not drop_motion:
            motion_tokens, motion_rope = self._framepack(motion_latents.to(self.device, self.dtype))
            tokens = torch.cat([tokens, motion_tokens], dim=1)
            mask = torch.cat([mask, torch.full((motion_tokens.shape[1],), 2, device=self.device, dtype=torch.long)])
            rope = (torch.cat([rope[0], motion_rope[0]], dim=0), torch.cat([rope[1], motion_rope[1]], dim=0))
        tokens = tokens + weights["trainable_cond_mask.weight"][mask].unsqueeze(0)
        del weights, target, reference, condition, mask
        self._release()
        return tokens, rope, grid, original_length

    def prepare_time_and_context(self, timestep: Any, text_context: Any) -> tuple[Any, Any, Any]:
        """Create S2V zero-timestep modulation and 512-token text context."""
        import torch
        import torch.nn.functional as functional

        timestep = timestep.reshape(1).to(device=self.device)
        times = torch.cat([timestep, torch.zeros_like(timestep)])
        time_names = (
            "time_embedding.0.weight", "time_embedding.0.bias",
            "time_embedding.2.weight", "time_embedding.2.bias",
            "time_projection.1.weight", "time_projection.1.bias",
        )
        weights = {name: self._weight(name) for name in time_names}
        time_input = self._sinusoidal_embedding(times).to(self.dtype)
        embedded = self._linear(
            time_input, weights["time_embedding.0.weight"], weights["time_embedding.0.bias"]
        )
        embedded = functional.silu(embedded)
        embedded = self._linear(
            embedded, weights["time_embedding.2.weight"], weights["time_embedding.2.bias"]
        )
        projected = functional.silu(embedded)
        projected = self._linear(
            projected, weights["time_projection.1.weight"], weights["time_projection.1.bias"]
        ).view(2, 6, DIM).float()
        head_embedding = embedded[:1].float()
        normal, zero = projected[:1], projected[1:]
        e0 = torch.stack([normal, zero], dim=2)
        del weights, time_input, embedded, projected, normal, zero
        self._release()

        context = text_context[:512].to(dtype=self.dtype)
        if context.shape[0] < 512:
            context = torch.cat(
                [context, torch.zeros((512 - context.shape[0], 4096), dtype=self.dtype)], dim=0
            )
        context = context.unsqueeze(0).to(self.device)
        text_names = (
            "text_embedding.0.weight", "text_embedding.0.bias",
            "text_embedding.2.weight", "text_embedding.2.bias",
        )
        weights = {name: self._weight(name) for name in text_names}
        context = self._linear(
            context, weights["text_embedding.0.weight"], weights["text_embedding.0.bias"]
        )
        context = functional.gelu(context, approximate="tanh")
        context = self._linear(
            context, weights["text_embedding.2.weight"], weights["text_embedding.2.bias"]
        )
        del weights
        self._release()
        return head_embedding, e0, context

    def output_head(self, x: Any, head_embedding: Any, grid: tuple[int, int, int]) -> Any:
        import torch

        weights = {
            "modulation": self._weight("head.modulation", fp32=True),
            "weight": self._weight("head.head.weight"),
            "bias": self._weight("head.head.bias"),
        }
        shift, scale = (weights["modulation"] + head_embedding.unsqueeze(1)).chunk(2, dim=1)
        normalized = self._layer_norm(x).float() * (1 + scale) + shift
        output = self._linear(normalized.to(self.dtype), weights["weight"], weights["bias"])
        frames, height, width = grid
        output = output.view(frames, height, width, *PATCH, 16)
        output = torch.einsum("fhwpqrc->cfphqwr", output)
        output = output.reshape(1, 16, frames * PATCH[0], height * PATCH[1], width * PATCH[2])
        del weights, normalized, x
        self._release()
        return output.float()

    def forward(
        self,
        noisy_latents: Any,
        timestep: Any,
        text_context: Any,
        reference_latents: Any,
        condition_latents: Any,
        motion_latents: Any,
        audio_input: Any,
        *,
        drop_motion: bool = True,
        emit: Any | None = None,
    ) -> Any:
        """One complete streamed Wan S2V denoiser evaluation."""
        import torch

        global_audio, local_audio = self.prepare_audio_embeddings(audio_input)
        tokens, rope, grid, original_length = self.prepare_tokens(
            noisy_latents,
            reference_latents,
            condition_latents,
            motion_latents,
            drop_motion=drop_motion,
        )
        head_embedding, e0, context = self.prepare_time_and_context(timestep, text_context)
        injector_index = 0
        with torch.inference_mode():
            for block_index in range(LAYERS):
                if emit is not None:
                    emit(
                        "generating", "transformer",
                        f"streaming Wan S2V block {block_index + 1}/{LAYERS}",
                    )
                weights = self._load_block(block_index)
                tokens = self._block(tokens, context, e0, original_length, rope, weights)
                del weights
                self._release()
                if block_index in AUDIO_INJECT_LAYERS:
                    tokens = self._audio_inject(
                        tokens, grid, global_audio, local_audio, injector_index
                    )
                    injector_index += 1
            tokens = tokens[:, :original_length]
            output = self.output_head(tokens, head_embedding, grid)
        del global_audio, local_audio, rope, head_embedding, e0, context
        self._release()
        return output

    def test_full_block(self, block_index: int = 0) -> dict[str, Any]:
        """Run an exact S2V block computation on a tiny two-token sequence."""
        import torch

        x = torch.zeros((1, 2, DIM), device=self.device, dtype=self.dtype)
        context = torch.zeros((1, 3, DIM), device=self.device, dtype=self.dtype)
        e0 = torch.zeros((1, 6, 2, DIM), device=self.device, dtype=torch.float32)
        cos, sin = self._standard_rope(2, 1, 1)
        weights = self._load_block(block_index)
        with torch.inference_mode():
            output = self._block(x, context, e0, 1, (cos, sin), weights)
            torch.mps.synchronize()
            result = {
                "shape": list(output.shape),
                "dtype": str(output.dtype),
                "finite": bool(torch.isfinite(output).all()),
                "mean": float(output.float().mean().cpu()),
            }
        del weights, output, x, context, e0, cos, sin
        self._release()
        return result
