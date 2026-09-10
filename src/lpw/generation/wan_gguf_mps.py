"""Experimental direct GGUF-to-MPS loader for the Wan 2.2 S2V transformer.

This module deliberately stops short of claiming full S2V inference.  It
provides the first backend layer: inspect the real GGUF, validate it against
the official S2V-14B architecture, dequantize one transformer block, place it
on MPS, exercise representative attention/FFN kernels, and report memory use.
"""

from __future__ import annotations

import argparse
import gc
import json
import platform
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OFFICIAL_S2V_14B = {
    "_class_name": "WanModel_S2V",
    "model_type": "s2v",
    "dim": 5120,
    "ffn_dim": 13824,
    "num_heads": 40,
    "num_layers": 40,
    "in_dim": 16,
    "out_dim": 16,
    "cond_dim": 16,
    "audio_dim": 1024,
    "num_audio_token": 4,
    "enable_adain": True,
    "enable_framepack": True,
    "enable_motioner": False,
}

OFFICIAL_AUDIO_INJECT_LAYERS = (0, 4, 8, 12, 16, 20, 24, 27, 30, 33, 36, 39)

BLOCK_TENSOR_SUFFIXES = frozenset(
    {
        "cross_attn.k.bias",
        "cross_attn.k.weight",
        "cross_attn.norm_k.weight",
        "cross_attn.norm_q.weight",
        "cross_attn.o.bias",
        "cross_attn.o.weight",
        "cross_attn.q.bias",
        "cross_attn.q.weight",
        "cross_attn.v.bias",
        "cross_attn.v.weight",
        "ffn.0.bias",
        "ffn.0.weight",
        "ffn.2.bias",
        "ffn.2.weight",
        "modulation",
        "norm3.bias",
        "norm3.weight",
        "self_attn.k.bias",
        "self_attn.k.weight",
        "self_attn.norm_k.weight",
        "self_attn.norm_q.weight",
        "self_attn.o.bias",
        "self_attn.o.weight",
        "self_attn.q.bias",
        "self_attn.q.weight",
        "self_attn.v.bias",
        "self_attn.v.weight",
    }
)


class ProbeError(RuntimeError):
    """A deterministic architecture or runtime probe failure."""


@dataclass(frozen=True)
class MemorySnapshot:
    label: str
    process_rss_bytes: int
    system_available_bytes: int
    mps_current_allocated_bytes: int
    mps_driver_allocated_bytes: int
    mps_recommended_max_bytes: int


def _optional_imports() -> tuple[Any, Any, Any, Any]:
    try:
        import numpy as np
        import psutil
        import torch
        from gguf import GGUFReader
    except ModuleNotFoundError as error:
        raise ProbeError(
            "install the direct backend dependencies with "
            "`python -m pip install -e '.[s2v-mps]'`"
        ) from error
    return np, psutil, torch, GGUFReader


def _tensor_torch_shape(tensor: Any) -> tuple[int, ...]:
    """Translate GGML's innermost-first dimensions to PyTorch order."""
    return tuple(int(value) for value in reversed(tensor.shape))


def _expected_block_shapes(config: dict[str, Any]) -> dict[str, tuple[int, ...]]:
    dim = int(config["dim"])
    ffn_dim = int(config["ffn_dim"])
    shapes: dict[str, tuple[int, ...]] = {}
    for attention in ("self_attn", "cross_attn"):
        for projection in ("q", "k", "v", "o"):
            shapes[f"{attention}.{projection}.weight"] = (dim, dim)
            shapes[f"{attention}.{projection}.bias"] = (dim,)
        shapes[f"{attention}.norm_q.weight"] = (dim,)
        shapes[f"{attention}.norm_k.weight"] = (dim,)
    shapes.update(
        {
            "ffn.0.weight": (ffn_dim, dim),
            "ffn.0.bias": (ffn_dim,),
            "ffn.2.weight": (dim, ffn_dim),
            "ffn.2.bias": (dim,),
            "modulation": (1, 6, dim),
            "norm3.weight": (dim,),
            "norm3.bias": (dim,),
        }
    )
    return shapes


def inspect_checkpoint(model_path: Path, config_path: Path) -> tuple[Any, dict[str, Any]]:
    """Validate GGUF names/shapes against Alibaba's official S2V-14B config."""
    _, _, _, GGUFReader = _optional_imports()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mismatches = {
        key: {"expected": expected, "actual": config.get(key)}
        for key, expected in OFFICIAL_S2V_14B.items()
        if config.get(key) != expected
    }
    actual_audio_layers = tuple(config.get("audio_inject_layers", ()))
    if actual_audio_layers != OFFICIAL_AUDIO_INJECT_LAYERS:
        mismatches["audio_inject_layers"] = {
            "expected": list(OFFICIAL_AUDIO_INJECT_LAYERS),
            "actual": list(actual_audio_layers),
        }
    if mismatches:
        raise ProbeError(f"checkpoint config does not match official S2V-14B: {mismatches}")

    reader = GGUFReader(model_path, "r")
    by_name = {tensor.name: tensor for tensor in reader.tensors}
    expected_shapes = _expected_block_shapes(config)
    block_errors: list[str] = []
    for block_index in range(int(config["num_layers"])):
        prefix = f"blocks.{block_index}."
        found = {name[len(prefix) :] for name in by_name if name.startswith(prefix)}
        missing = BLOCK_TENSOR_SUFFIXES - found
        extra = found - BLOCK_TENSOR_SUFFIXES
        if missing or extra:
            block_errors.append(
                f"block {block_index}: missing={sorted(missing)}, extra={sorted(extra)}"
            )
            continue
        for suffix, expected_shape in expected_shapes.items():
            actual_shape = _tensor_torch_shape(by_name[prefix + suffix])
            if actual_shape != expected_shape:
                block_errors.append(
                    f"{prefix}{suffix}: expected {expected_shape}, got {actual_shape}"
                )
    if block_errors:
        raise ProbeError("GGUF block mapping failed: " + "; ".join(block_errors[:20]))

    prefix_counts = Counter(tensor.name.split(".", 1)[0] for tensor in reader.tensors)
    quant_counts = Counter(tensor.tensor_type.name for tensor in reader.tensors)
    block_zero_map = []
    for suffix in sorted(BLOCK_TENSOR_SUFFIXES):
        tensor = by_name[f"blocks.0.{suffix}"]
        block_zero_map.append(
            {
                "gguf_name": tensor.name,
                # This GGUF preserves the official PyTorch state-dict name.
                "official_state_dict_name": tensor.name,
                "torch_shape": list(_tensor_torch_shape(tensor)),
                "gguf_type": tensor.tensor_type.name,
            }
        )
    report = {
        "architecture": "WanModel_S2V",
        "architecture_match": True,
        "model_path": str(model_path.resolve()),
        "file_bytes": model_path.stat().st_size,
        "tensor_count": len(reader.tensors),
        "tensor_types": dict(sorted(quant_counts.items())),
        "prefix_counts": dict(sorted(prefix_counts.items())),
        "main_transformer_blocks": config["num_layers"],
        "tensors_per_main_block": len(BLOCK_TENSOR_SUFFIXES),
        "audio_injector_count": prefix_counts.get("audio_injector", 0) // 12,
        "framepack_present": prefix_counts.get("frame_packer", 0) == 6,
        "block_0_tensor_map": block_zero_map,
    }
    return reader, report


def _snapshot(label: str, torch: Any, psutil: Any) -> MemorySnapshot:
    process = psutil.Process()
    virtual = psutil.virtual_memory()
    return MemorySnapshot(
        label=label,
        process_rss_bytes=process.memory_info().rss,
        system_available_bytes=virtual.available,
        mps_current_allocated_bytes=int(torch.mps.current_allocated_memory()),
        mps_driver_allocated_bytes=int(torch.mps.driver_allocated_memory()),
        mps_recommended_max_bytes=int(torch.mps.recommended_max_memory()),
    )


def _require_mps(torch: Any) -> None:
    if platform.system() != "Darwin" or platform.machine() not in {"arm64", "aarch64"}:
        raise ProbeError("the direct local probe requires Apple Silicon macOS")
    if not torch.backends.mps.is_available():
        raise ProbeError("torch.backends.mps.is_available() is false")
    if not torch.backends.mps.is_built():
        raise ProbeError("this PyTorch build does not include MPS")


def load_block_to_mps(reader: Any, block_index: int, torch: Any) -> dict[str, Any]:
    """Stream-dequantize one official Wan S2V block and retain it in MPS BF16."""
    from gguf.quants import dequantize

    prefix = f"blocks.{block_index}."
    source = {tensor.name: tensor for tensor in reader.tensors if tensor.name.startswith(prefix)}
    found = {name[len(prefix) :] for name in source}
    if found != BLOCK_TENSOR_SUFFIXES:
        raise ProbeError(f"block {block_index} does not have the official 27-tensor layout")

    loaded: dict[str, Any] = {}
    for suffix in sorted(BLOCK_TENSOR_SUFFIXES):
        tensor = source[prefix + suffix]
        # gguf dequantization is CPU/NumPy.  Only one temporary FP32 tensor is
        # alive at a time; the retained MPS copy uses BF16.
        array = dequantize(tensor.data, tensor.tensor_type)
        if not array.flags.writeable:
            array = array.copy()
        value = torch.from_numpy(array).to(device="mps", dtype=torch.bfloat16)
        loaded[suffix] = value
        del value, array
    torch.mps.synchronize()
    return loaded


def smoke_test_block_kernels(weights: dict[str, Any], torch: Any) -> dict[str, Any]:
    """Exercise the loaded block's real projections with a one-token input.

    This validates MPS BF16 linear, SDPA, GELU and residual-compatible shapes.
    It is not a semantic Wan denoising pass (RoPE, timestep modulation, audio
    injection and FramePack are intentionally outside this bounded probe).
    """
    functional = torch.nn.functional
    dim = weights["self_attn.q.weight"].shape[1]
    heads = 40
    head_dim = dim // heads
    x = torch.zeros((1, 1, dim), device="mps", dtype=torch.bfloat16)

    q = functional.linear(x, weights["self_attn.q.weight"], weights["self_attn.q.bias"])
    k = functional.linear(x, weights["self_attn.k.weight"], weights["self_attn.k.bias"])
    v = functional.linear(x, weights["self_attn.v.weight"], weights["self_attn.v.bias"])
    q = q.view(1, 1, heads, head_dim).transpose(1, 2)
    k = k.view(1, 1, heads, head_dim).transpose(1, 2)
    v = v.view(1, 1, heads, head_dim).transpose(1, 2)
    attention = functional.scaled_dot_product_attention(q, k, v)
    attention = attention.transpose(1, 2).reshape(1, 1, dim)
    attention_out = functional.linear(
        attention, weights["self_attn.o.weight"], weights["self_attn.o.bias"]
    )

    hidden = functional.linear(x, weights["ffn.0.weight"], weights["ffn.0.bias"])
    hidden = functional.gelu(hidden, approximate="tanh")
    ffn_out = functional.linear(hidden, weights["ffn.2.weight"], weights["ffn.2.bias"])
    checksum = float((attention_out.float().mean() + ffn_out.float().mean()).cpu())
    torch.mps.synchronize()
    result = {
        "status": "passed",
        "device": str(attention_out.device),
        "dtype": str(attention_out.dtype),
        "attention_output_shape": list(attention_out.shape),
        "ffn_output_shape": list(ffn_out.shape),
        "finite": bool(torch.isfinite(attention_out).all() and torch.isfinite(ffn_out).all()),
        "checksum": checksum,
    }
    del x, q, k, v, attention, attention_out, hidden, ffn_out
    return result


def run_probe(model_path: Path, config_path: Path, block_index: int) -> dict[str, Any]:
    _, psutil, torch, _ = _optional_imports()
    _require_mps(torch)
    started = time.monotonic()
    snapshots = [_snapshot("before_metadata", torch, psutil)]
    reader, architecture = inspect_checkpoint(model_path, config_path)
    snapshots.append(_snapshot("after_metadata", torch, psutil))
    weights = load_block_to_mps(reader, block_index, torch)
    snapshots.append(_snapshot("after_block_load", torch, psutil))
    kernel_test = smoke_test_block_kernels(weights, torch)
    snapshots.append(_snapshot("after_kernel_smoke_test", torch, psutil))

    retained_bytes = sum(tensor.nelement() * tensor.element_size() for tensor in weights.values())
    all_main_blocks_bf16_estimate = retained_bytes * int(architecture["main_transformer_blocks"])
    del weights, reader
    gc.collect()
    torch.mps.empty_cache()
    torch.mps.synchronize()
    snapshots.append(_snapshot("after_release", torch, psutil))
    base = snapshots[0]
    loaded = snapshots[2]
    return {
        "status": "passed",
        "scope": "one-block GGUF dequantization and MPS kernel feasibility",
        "full_inference_ready": False,
        "block_index": block_index,
        "architecture": architecture,
        "block_retained_bf16_bytes": retained_bytes,
        "estimated_all_main_blocks_bf16_bytes": all_main_blocks_bf16_estimate,
        "all_main_blocks_fit_mps_recommended_limit": (
            all_main_blocks_bf16_estimate <= base.mps_recommended_max_bytes
        ),
        "mps_allocated_delta_bytes": (
            loaded.mps_current_allocated_bytes - base.mps_current_allocated_bytes
        ),
        "process_rss_delta_bytes": loaded.process_rss_bytes - base.process_rss_bytes,
        "kernel_test": kernel_test,
        "memory_snapshots": [asdict(snapshot) for snapshot in snapshots],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "remaining_backend_work": [
            "quantized layer streaming across all 40 blocks",
            "RoPE and timestep modulation parity",
            "UMT5 GGUF text encoding",
            "Wav2Vec2 and causal audio injection",
            "FramePack reference conditioning",
            "scheduler loop and VAE encode/decode",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--block", type=int, default=0)
    parser.add_argument("--report", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_probe(args.model.resolve(), args.config.resolve(), args.block)
    except (OSError, ProbeError, RuntimeError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, indent=2), file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
