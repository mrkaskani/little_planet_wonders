#!/usr/bin/env python3
"""Generate non-neutral profile-reference auditions from locked neutral voices."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import random
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import yaml
from qwen_tts import Qwen3TTSModel


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_ROOT = PROJECT_ROOT / "src/lpw/context/projects/classroom"
MODEL_DIR = PROJECT_ROOT / "models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs/qwen3-tts/cloned-reference-auditions"
PROFILES = {
    "yoyo": CONTEXT_ROOT / "characters/yoyo/voice-profile.yaml",
    "riri": CONTEXT_ROOT / "characters/riri/voice-profile.yaml",
}
SEED_BASES = {"yoyo": 271_828, "riri": 314_159}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--character",
        action="append",
        choices=tuple(PROFILES),
        help="Generate one character; repeat as needed. Defaults to both.",
    )
    parser.add_argument("--language", default="English")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--batch-id",
        default=datetime.now().strftime("%Y%m%d-%H%M%S-%f"),
        help="Immutable audition batch directory name.",
    )
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_character(character: str) -> dict[str, object]:
    profile_path = PROFILES[character]
    payload = yaml.safe_load(profile_path.read_text())
    references = payload["references"]
    neutral = references["neutral-friendly"]
    neutral_audio = (CONTEXT_ROOT / neutral["path"]).resolve()
    if not neutral_audio.is_file():
        raise SystemExit(
            f"Locked neutral reference is missing for {character}: {neutral_audio}"
        )
    jobs = []
    for index, (name, reference) in enumerate(references.items()):
        if name == "neutral-friendly":
            continue
        jobs.append(
            {
                "name": name,
                "text": str(reference["text"]).strip(),
                "seed": SEED_BASES[character] + index * 101,
            }
        )
    return {
        "character": character,
        "profile": str(profile_path),
        "neutral_audio": neutral_audio,
        "neutral_text": str(neutral["text"]).strip(),
        "neutral_sha256": sha256(neutral_audio),
        "jobs": jobs,
    }


def write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    if not (MODEL_DIR / "model.safetensors").is_file():
        raise SystemExit("Base weights are missing; run scripts/qwen3_tts/download_base.sh")

    characters = args.character or list(PROFILES)
    selected = [load_character(character) for character in characters]
    batch_root = args.output_root.expanduser().resolve() / args.batch_id
    if batch_root.exists():
        raise SystemExit(f"Audition batch already exists and is immutable: {batch_root}")
    batch_root.mkdir(parents=True)

    manifest: dict[str, object] = {
        "batch_id": args.batch_id,
        "status": "running",
        "model": str(MODEL_DIR),
        "mode": "voice-clone-from-locked-neutral",
        "language": args.language,
        "characters": [],
    }
    for config in selected:
        character_record = {
            "character": config["character"],
            "profile": config["profile"],
            "neutral_audio": str(config["neutral_audio"]),
            "neutral_text": config["neutral_text"],
            "neutral_sha256": config["neutral_sha256"],
            "auditions": [],
        }
        manifest["characters"].append(character_record)  # type: ignore[union-attr]
        for job in config["jobs"]:  # type: ignore[union-attr]
            output = batch_root / str(config["character"]) / f"{job['name']}-seed-{job['seed']}.wav"
            character_record["auditions"].append(
                {
                    **job,
                    "output": str(output),
                    "status": "pending",
                }
            )
    write_manifest(batch_root / "manifest.json", manifest)

    use_mps = torch.backends.mps.is_available()
    device = "mps" if use_mps else "cpu"
    dtype = torch.float16 if use_mps else torch.float32
    total = sum(len(config["jobs"]) for config in selected)  # type: ignore[arg-type]
    print(f"Loading Base cloning model once on {device} for {total} audition(s)...", flush=True)
    model = Qwen3TTSModel.from_pretrained(
        str(MODEL_DIR),
        device_map=device,
        dtype=dtype,
        attn_implementation="eager",
    )

    for config, character_record in zip(selected, manifest["characters"], strict=True):  # type: ignore[arg-type]
        character = str(config["character"])
        print(f"Preparing locked clone identity for {character}...", flush=True)
        clone_prompt = model.create_voice_clone_prompt(
            ref_audio=str(config["neutral_audio"]),
            ref_text=str(config["neutral_text"]),
            x_vector_only_mode=False,
        )
        for audition in character_record["auditions"]:
            seed = int(audition["seed"])
            seed_everything(seed)
            print(f"Generating {character}/{audition['name']} (seed={seed})...", flush=True)
            wavs, sample_rate = model.generate_voice_clone(
                text=str(audition["text"]),
                language=args.language,
                voice_clone_prompt=clone_prompt,
                non_streaming_mode=True,
            )
            output = Path(str(audition["output"]))
            output.parent.mkdir(parents=True, exist_ok=True)
            sf.write(output, wavs[0], sample_rate)
            audition["status"] = "generated"
            audition["sample_rate"] = sample_rate
            write_manifest(batch_root / "manifest.json", manifest)
            gc.collect()
            if use_mps:
                torch.mps.empty_cache()

    manifest["status"] = "complete"
    write_manifest(batch_root / "manifest.json", manifest)
    print(f"Cloned-reference auditions: {batch_root}")
    print("Listen before approving any non-neutral reference.")


if __name__ == "__main__":
    main()
