"""Layer-streamed UMT5-XXL GGUF text encoder for Apple MPS."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .gguf_stream import GGUFStore


class UMT5GGUFEncoder:
    """Execute the 24-layer Wan UMT5 encoder without resident model weights."""

    def __init__(self, gguf_path: str | Path, tokenizer_path: str | Path, device: str = "mps"):
        import torch
        from transformers import AutoTokenizer

        self.store = GGUFStore(gguf_path)
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(Path(tokenizer_path).expanduser().resolve()), local_files_only=True
        )
        self.device = torch.device(device)
        self.dim = 4096
        self.ffn_dim = 10240
        self.heads = 64
        self.head_dim = 64
        self.layers = 24
        self.buckets = 32
        self.eps = 1e-6
        self._validate()

    def _validate(self) -> None:
        required = {"token_embd.weight", "enc.output_norm.weight"}
        for index in range(self.layers):
            prefix = f"enc.blk.{index}."
            required.update(
                prefix + suffix
                for suffix in (
                    "attn_q.weight",
                    "attn_k.weight",
                    "attn_v.weight",
                    "attn_o.weight",
                    "attn_norm.weight",
                    "attn_rel_b.weight",
                    "ffn_gate.weight",
                    "ffn_up.weight",
                    "ffn_down.weight",
                    "ffn_norm.weight",
                )
            )
        self.store.require(required)

    def _rms_norm(self, x: Any, weight: Any) -> Any:
        import torch

        normalized = x.float() * torch.rsqrt(x.float().pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return normalized.to(weight.dtype) * weight

    def _relative_position_bucket(self, relative_position: Any) -> Any:
        import torch

        half_buckets = self.buckets // 2
        buckets = (relative_position > 0).long() * half_buckets
        distance = torch.abs(relative_position)
        max_exact = half_buckets // 2
        large = max_exact + (
            torch.log(distance.float().clamp_min(1) / max_exact)
            / math.log(128 / max_exact)
            * (half_buckets - max_exact)
        ).long()
        large = torch.minimum(large, torch.full_like(large, half_buckets - 1))
        return buckets + torch.where(distance < max_exact, distance, large)

    def _position_bias(self, length: int, embedding: Any) -> Any:
        import torch

        positions = torch.arange(length, device=self.device)
        relative = positions.unsqueeze(0) - positions.unsqueeze(1)
        buckets = self._relative_position_bucket(relative)
        return embedding[buckets].permute(2, 0, 1).unsqueeze(0).contiguous()

    @staticmethod
    def _gated_gelu(x: Any) -> Any:
        import torch

        return 0.5 * x * (
            1.0 + torch.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x.pow(3)))
        )

    def _load_layer(self, index: int) -> dict[str, Any]:
        import torch

        prefix = f"enc.blk.{index}."
        return {
            suffix: self.store.tensor(prefix + suffix, device=str(self.device), dtype=torch.bfloat16)
            for suffix in (
                "attn_q.weight",
                "attn_k.weight",
                "attn_v.weight",
                "attn_o.weight",
                "attn_norm.weight",
                "attn_rel_b.weight",
                "ffn_gate.weight",
                "ffn_up.weight",
                "ffn_down.weight",
                "ffn_norm.weight",
            )
        }

    def _layer(self, x: Any, weights: dict[str, Any]) -> Any:
        import torch
        import torch.nn.functional as functional

        batch, length, _ = x.shape
        normalized = self._rms_norm(x, weights["attn_norm.weight"])
        q = functional.linear(normalized, weights["attn_q.weight"])
        k = functional.linear(normalized, weights["attn_k.weight"])
        v = functional.linear(normalized, weights["attn_v.weight"])
        q = q.view(batch, length, self.heads, self.head_dim).transpose(1, 2)
        k = k.view(batch, length, self.heads, self.head_dim).transpose(1, 2)
        v = v.view(batch, length, self.heads, self.head_dim).transpose(1, 2)
        bias = self._position_bias(length, weights["attn_rel_b.weight"])
        attended = functional.scaled_dot_product_attention(q, k, v, attn_mask=bias, scale=1.0)
        attended = attended.transpose(1, 2).reshape(batch, length, self.dim)
        x = x + functional.linear(attended, weights["attn_o.weight"])

        normalized = self._rms_norm(x, weights["ffn_norm.weight"])
        gate = self._gated_gelu(functional.linear(normalized, weights["ffn_gate.weight"]))
        up = functional.linear(normalized, weights["ffn_up.weight"])
        x = x + functional.linear(gate * up, weights["ffn_down.weight"])
        return x

    def encode(self, text: str, max_length: int = 512, emit: Any | None = None) -> Any:
        import torch

        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        ids = encoded["input_ids"][0]
        unique_ids, inverse = torch.unique(ids, sorted=True, return_inverse=True)
        selected = self.store.tensor("token_embd.weight", rows=unique_ids.numpy())
        x = selected[inverse].unsqueeze(0).to(device=self.device, dtype=torch.bfloat16)
        del selected, unique_ids, inverse

        with torch.inference_mode():
            for index in range(self.layers):
                if emit is not None:
                    emit("loading", "text", f"streaming UMT5 layer {index + 1}/{self.layers}")
                weights = self._load_layer(index)
                x = self._layer(x, weights)
                del weights
                torch.mps.synchronize()
                torch.mps.empty_cache()
            output_norm = self.store.tensor(
                "enc.output_norm.weight", device=str(self.device), dtype=torch.bfloat16
            )
            x = self._rms_norm(x, output_norm)
            del output_norm
            result = x.squeeze(0).to("cpu")
        del x
        torch.mps.empty_cache()
        torch.mps.synchronize()
        return result
