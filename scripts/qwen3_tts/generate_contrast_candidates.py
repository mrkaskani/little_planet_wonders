#!/usr/bin/env python3
"""Generate immutable matched-text VoiceDesign batches for contrast testing."""

from __future__ import annotations

import argparse
import gc
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import yaml
from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_ROOT = PROJECT_ROOT / "src/lpw/context/projects/riri-yoyo"
MODEL_DIR = PROJECT_ROOT / "models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
SPEAKER_MODEL_DIR = PROJECT_ROOT / "models/speaker-embeddings/wavlm-base-plus-sv"
ANALYZER = Path(__file__).resolve().with_name("analyze_voice_contrast.py")
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs/qwen3-tts/contrast-batches"
DEFAULT_TEXT = (
    "Hello! I'm happy to see you. It's a lovely day. "
    "Shall we look around together?"
)
CHARACTERS = {
    "yoyo": {
        "profile": CONTEXT_ROOT / "characters/yoyo/voice-profile.yaml",
        "seed": 271828,
    },
    "riri": {
        "profile": CONTEXT_ROOT / "characters/riri/voice-profile.yaml",
        "seed": 314159,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=8, help="Candidates per character.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Same audition text for both families.")
    parser.add_argument("--language", default="English")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.9,
        help="Talker sampling temperature (official checkpoint default: 0.9).",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=1.0,
        help="Nucleus-sampling probability mass (default: 1.0).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help="Top-k talker sampling cutoff (default: 50).",
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        default=1.05,
        help="Audio-token repetition penalty (default: 1.05).",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--batch-id",
        help="Immutable batch name; defaults to a timestamp with microseconds.",
    )
    parser.add_argument(
        "--seed-offset",
        type=int,
        help="Added to both seed families; defaults to a recorded time-derived value.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume missing files in an explicit existing batch without overwriting WAVs.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Generate WAVs and manifest only; automatic Markdown analysis is enabled by default.",
    )
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def neutral_prompt(profile_path: Path) -> str:
    payload = yaml.safe_load(profile_path.read_text())
    prompt = str(payload["references"]["neutral-friendly"]["prompt"]).strip()
    if not prompt:
        raise SystemExit(f"Neutral prompt is empty: {profile_path}")
    return prompt


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def analyze_batch(batch_root: Path) -> None:
    print(f"Analyzing completed batch: {batch_root}", flush=True)
    subprocess.run(
        [
            sys.executable,
            str(ANALYZER),
            "--batch-dir",
            str(batch_root),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> None:
    args = parse_args()
    if args.samples < 2:
        raise SystemExit("--samples must be at least 2 so contrast can be compared")
    if args.temperature <= 0:
        raise SystemExit("--temperature must be greater than zero")
    if not 0 < args.top_p <= 1:
        raise SystemExit("--top-p must be in the interval (0, 1]")
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")
    if args.repetition_penalty <= 0:
        raise SystemExit("--repetition-penalty must be greater than zero")

    sampling = {
        "do_sample": True,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "repetition_penalty": args.repetition_penalty,
    }
    if not args.skip_analysis and not (SPEAKER_MODEL_DIR / "config.json").is_file():
        raise SystemExit(
            "Automatic analysis requires the local WavLM speaker model.\n"
            "Run scripts/qwen3_tts/voice-contrast.sh download-analyzer first, "
            "or pass --skip-analysis."
        )

    output_root = args.output_root.expanduser().resolve()
    batch_id = args.batch_id or datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", batch_id):
        raise SystemExit("--batch-id may contain only letters, numbers, dot, underscore, and hyphen")
    batch_root = output_root / batch_id
    manifest_path = batch_root / "manifest.json"

    if args.resume:
        if not args.batch_id:
            raise SystemExit("--resume requires an explicit --batch-id")
        if not manifest_path.is_file():
            raise SystemExit(f"Cannot resume; manifest is missing: {manifest_path}")
        manifest = json.loads(manifest_path.read_text())
        seed_offset = int(manifest["seed_offset"])
        if int(manifest["samples_per_character"]) != args.samples:
            raise SystemExit(
                f"Resume sample mismatch: batch has {manifest['samples_per_character']}, "
                f"command requested {args.samples}"
            )
        if str(manifest["text"]) != args.text:
            raise SystemExit("Resume audition text does not match the batch manifest")
        # Batches created before sampling controls were exposed used these
        # same checkpoint defaults, so they remain resumable.
        recorded_sampling = manifest.get(
            "sampling",
            {
                "do_sample": True,
                "temperature": 0.9,
                "top_p": 1.0,
                "top_k": 50,
                "repetition_penalty": 1.05,
            },
        )
        if recorded_sampling != sampling:
            raise SystemExit(
                "Resume sampling settings do not match the batch manifest; "
                "repeat the original sampling arguments"
            )
    else:
        if batch_root.exists():
            raise SystemExit(
                f"Batch already exists and is immutable: {batch_root}\n"
                "Choose a new --batch-id, or use --resume to fill missing files."
            )
        seed_offset = args.seed_offset
        if seed_offset is None:
            seed_offset = time.time_ns() % 1_000_000_000
        batch_root.mkdir(parents=True)
        manifest = {
            "batch_id": batch_id,
            "status": "planned",
            "samples_per_character": args.samples,
            "seed_offset": seed_offset,
            "text": args.text,
            "language": args.language,
            "sampling": sampling,
            "candidates": [],
        }

    jobs: list[dict[str, object]] = []
    for character, config in CHARACTERS.items():
        prompt = neutral_prompt(Path(config["profile"]))
        for offset in range(args.samples):
            seed = int(config["seed"]) + seed_offset + offset
            output = batch_root / character / f"{character}-seed-{seed}.wav"
            jobs.append(
                {
                    "character": character,
                    "seed": seed,
                    "text": args.text,
                    "prompt": prompt,
                    "file": str(output),
                    "status": "generated" if output.is_file() else "pending",
                }
            )

    pending = [job for job in jobs if job["status"] == "pending"]
    manifest["candidates"] = jobs
    manifest["status"] = "complete" if not pending else "running"
    write_manifest(manifest_path, manifest)
    if not pending:
        print(f"Batch is already complete; nothing was overwritten: {batch_root}", flush=True)
        if not args.skip_analysis:
            analyze_batch(batch_root)
        return

    if not (MODEL_DIR / "model.safetensors").is_file():
        raise SystemExit("VoiceDesign weights are missing; run scripts/qwen3_tts/download.sh")

    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    dtype = torch.float16 if use_mps else torch.float32
    print(f"Batch: {batch_id}")
    print(f"Loading VoiceDesign once on {device} for {len(pending)} pending candidates...")
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL_DIR),
        device_map=device,
        dtype=dtype,
        attn_implementation="eager",
    )

    for job in pending:
        seed = int(job["seed"])
        seed_everything(seed)
        print(f"Generating {job['character']} seed {seed}...")
        wavs, sample_rate = model.generate_voice_design(
            text=str(job["text"]),
            instruct=str(job["prompt"]),
            language=args.language,
            **sampling,
        )
        output = Path(str(job["file"]))
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output, wavs[0], sample_rate)
        job["status"] = "generated"
        job["sample_rate"] = sample_rate
        write_manifest(manifest_path, manifest)
        print(f"Wrote {output}")
        gc.collect()
        if use_mps:
            torch.mps.empty_cache()

    manifest["status"] = "complete"
    write_manifest(manifest_path, manifest)
    print(f"Manifest: {manifest_path}")
    del model
    gc.collect()
    if use_mps:
        torch.mps.empty_cache()
    if args.skip_analysis:
        print("Analysis skipped by request.")
    else:
        analyze_batch(batch_root)
        print(
            "Analysis complete: "
            f"{PROJECT_ROOT / 'outputs/qwen3-tts/contrast-analysis' / batch_id / 'voice-contrast.md'}"
        )


if __name__ == "__main__":
    main()
