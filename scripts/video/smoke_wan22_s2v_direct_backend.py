#!/usr/bin/env python3
"""Run a reduced-step end-to-end direct-backend validation render."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from lpw.generation.wan_s2v_backend import DirectWanS2VBackend


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--model-root", type=Path, required=True)
    value.add_argument("--reference", type=Path, required=True)
    value.add_argument("--audio", type=Path, required=True)
    value.add_argument("--output", type=Path, required=True)
    value.add_argument("--prompt", default="A character speaks gently in a moonlit garden.")
    value.add_argument("--negative-prompt", default="identity drift, malformed face, camera jump")
    value.add_argument("--prompt-manifest", type=Path)
    value.add_argument("--segment-id", default="segment-001")
    value.add_argument("--width", type=int, default=16)
    value.add_argument("--height", type=int, default=16)
    value.add_argument("--steps", type=int, default=1)
    value.add_argument("--decode-checkpoint", type=Path)
    return value


def main() -> int:
    args = parser().parse_args()
    root = args.model_root.expanduser().resolve()
    started = time.monotonic()
    prompt = args.prompt
    negative_prompt = args.negative_prompt
    if args.prompt_manifest is not None:
        import yaml

        manifest = yaml.safe_load(args.prompt_manifest.expanduser().read_text())
        selected = next(
            job for job in manifest["jobs"] if job["id"] == args.segment_id
        )
        prompt = f'{manifest["global_positive_prompt"]} {selected["performance_prompt"]}'
        negative_prompt = manifest["global_negative_prompt"]

    def emit(status: str, phase: str, message: str, **fields) -> None:
        if phase != "transformer":
            print(json.dumps({"status": status, "phase": phase, "message": message, **fields}), flush=True)

    config = {
        "model_gguf": str(root / "diffusion_models/Wan2.2-S2V-14B-Q4_K_S.gguf"),
        "vae_path": str(root / "vae/wan_2.1_vae.safetensors"),
        "text_encoder_path": str(root / "text_encoders/umt5-xxl-encoder-Q4_K_S.gguf"),
        "tokenizer_path": str(root / "text_encoders/umt5-tokenizer"),
        "audio_encoder_path": str(root / "audio_encoders/wav2vec2_large_english_fp16.safetensors"),
    }
    backend = DirectWanS2VBackend(config, emit, lambda phase: None)
    args.output.mkdir(parents=True, exist_ok=True)
    job = {
            "job_id": "direct-backend-smoke",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "reference_image": str(args.reference.resolve()),
            "audio_path": str(args.audio.resolve()),
            "seed": 42,
            "width": args.width,
            "height": args.height,
            "frame_count": 81,
            "fps": 16,
            "steps": args.steps,
            "cfg": 6.0,
            "checkpoint_directory": str((args.output.parent / "checkpoints").resolve()),
        }
    if args.decode_checkpoint is not None:
        job["decode_checkpoint"] = str(args.decode_checkpoint.expanduser().resolve())
    count = backend.generate_to_directory(
        job,
        str(args.output.resolve()),
        emit,
    )
    report = {
        "status": "passed",
        "scope": "reduced-step end-to-end direct S2V backend validation",
        "frames": count,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "decode_only": args.decode_checkpoint is not None,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    (args.output / "smoke-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
