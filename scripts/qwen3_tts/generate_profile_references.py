#!/usr/bin/env python3
"""Generate VoiceDesign candidates from every reference in a voice profile."""

from __future__ import annotations

import argparse
import gc
import random
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import yaml
from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "qwen3-tts"
    / "Qwen3-TTS-12Hz-1.7B-VoiceDesign"
)
REQUIRED_REFERENCE_FIELDS = {"path", "target_duration_seconds", "text", "prompt"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument(
        "--reference",
        action="append",
        dest="references",
        help="Generate only this reference name; repeat to select several.",
    )
    parser.add_argument("--language", default="English")
    parser.add_argument("--seed-base", type=int, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "qwen3-tts" / "candidates",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def load_profile(path: Path) -> tuple[str, dict[str, dict[str, object]]]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"Voice profile not found: {resolved}")
    payload = yaml.safe_load(resolved.read_text())
    character = payload.get("id")
    references = payload.get("references")
    if not isinstance(character, str) or not character:
        raise SystemExit(f"Voice profile has no character id: {resolved}")
    if not isinstance(references, dict) or not references:
        raise SystemExit(f"Voice profile has no references: {resolved}")
    for name, reference in references.items():
        if not isinstance(reference, dict):
            raise SystemExit(f"Reference {name!r} must be a mapping")
        missing = REQUIRED_REFERENCE_FIELDS - set(reference)
        if missing:
            raise SystemExit(f"Reference {name!r} is missing: {', '.join(sorted(missing))}")
    return character, references


def main() -> None:
    args = parse_args()
    character, all_references = load_profile(args.profile)
    selected_names = args.references or list(all_references)
    unknown = [name for name in selected_names if name not in all_references]
    if unknown:
        raise SystemExit(
            f"Unknown reference(s): {', '.join(unknown)}. "
            f"Available: {', '.join(all_references)}"
        )

    jobs: list[tuple[str, dict[str, object], int, Path]] = []
    output_root = args.output_root.expanduser().resolve() / character
    for index, name in enumerate(all_references):
        if name not in selected_names:
            continue
        reference = all_references[name]
        seed = args.seed_base + index * 101
        output = output_root / f"{name}-seed-{seed}.wav"
        if output.exists() and not args.force:
            raise SystemExit(f"Output exists; use --force to replace it: {output}")
        jobs.append((name, reference, seed, output))

    if not (MODEL_DIR / "model.safetensors").is_file():
        raise SystemExit("VoiceDesign weights are missing; run scripts/qwen3_tts/download.sh")

    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    dtype = torch.float16 if use_mps else torch.float32
    print(f"Loading VoiceDesign once on {device} for {len(jobs)} reference(s)...")
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL_DIR),
        device_map=device,
        dtype=dtype,
        attn_implementation="eager",
    )

    for name, reference, seed, output in jobs:
        seed_everything(seed)
        print(f"Generating {character}/{name} (seed={seed})...")
        wavs, sample_rate = model.generate_voice_design(
            text=str(reference["text"]).strip(),
            instruct=str(reference["prompt"]).strip(),
            language=args.language,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output, wavs[0], sample_rate)
        print(f"Wrote {output}")
        gc.collect()
        if use_mps:
            torch.mps.empty_cache()

    print("Candidates generated. Listen before approving them as profile references.")


if __name__ == "__main__":
    main()
