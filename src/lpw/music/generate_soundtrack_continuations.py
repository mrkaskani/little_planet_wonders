#!/usr/bin/env python3
"""Extend the preserved third section of approved soundtrack references."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
import wave
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CONFIG = (
    REPO_ROOT / "src/lpw/context/projects/riri-yoyo/audios/soundtrack-continuations.yaml"
)
ORCHESTRATOR = REPO_ROOT / "scripts/orchestrator/audio_generator.py"


def fail(message: str) -> "None":
    raise SystemExit(f"error: {message}")


def safe_relative(value: str, suffix: str | None = None) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        fail(f"unsafe relative path: {value}")
    if suffix and path.suffix.lower() != suffix:
        fail(f"expected a {suffix} path: {value}")
    return Path(*path.parts)


def wav_metadata(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        return {
            "channels": audio.getnchannels(),
            "sample_rate_hz": audio.getframerate(),
            "sample_width_bytes": audio.getsampwidth(),
            "duration_seconds": round(audio.getnframes() / audio.getframerate(), 3),
            "frames": audio.getnframes(),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }


def run_sox(arguments: list[str]) -> None:
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required for soundtrack continuation generation")
    subprocess.run([sox, *arguments], check=True)


def extract_reference_section(source: Path, output: Path, start_seconds: float) -> float:
    duration = float(wav_metadata(source)["duration_seconds"])
    if start_seconds < 0 or start_seconds >= duration:
        fail(f"third-section start is outside the source soundtrack: {source}")
    section_seconds = duration - start_seconds
    run_sox(
        [
            str(source), "-r", "44100", "-b", "16", "-c", "2", str(output),
            "trim", f"{start_seconds:.6f}", f"{section_seconds:.6f}",
            "rate", "-v", "44100",
        ]
    )
    return float(wav_metadata(output)["duration_seconds"])


def extract_generated_continuation(
    source: Path,
    output: Path,
    context_seconds: float,
    target_seconds: float,
    ending_fade_seconds: float,
) -> None:
    run_sox(
        [
            str(source),
            str(output),
            "trim", f"{context_seconds:.6f}", f"{target_seconds:.6f}",
            "fade", "t", "0", f"{target_seconds:.6f}", f"{ending_fade_seconds:.6f}",
        ]
    )


def conform_audio(source: Path, output: Path, generator: dict[str, object]) -> None:
    channels = 2 if generator["channels"] == "stereo" else 1
    output.parent.mkdir(parents=True, exist_ok=True)
    run_sox(
        [
            str(source),
            "-r", str(generator["sample_rate"]),
            "-b", str(generator["bit_depth"]),
            "-c", str(channels),
            str(output),
            "gain", "-3",
            "rate", "-v", str(generator["sample_rate"]),
            "gain", "-n", str(generator["peak_ceiling_dbfs"]),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extend the exact third part of each reference to 30 seconds."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--track", action="append", default=[])
    parser.add_argument(
        "--seed",
        type=int,
        help="use a reproducible base seed; omitted means a fresh random seed per track",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generator = config["generator"]
    if generator["strategy"] != "preserve-third-part-and-continue":
        fail("unsupported soundtrack continuation strategy")
    if generator["model"] != "medium" or generator["decoder"] != "same-l":
        fail("third-part continuation requires Stable Audio 3 Medium with SAME-L")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")
    target_seconds = float(generator["target_seconds"])

    project_root = (REPO_ROOT / safe_relative(str(generator["project_root"]))).resolve()
    tracks = [
        track for track in config["soundtracks"]
        if not args.track or track["id"] in args.track
    ]
    if not tracks:
        fail("no continuation soundtrack matched the selection")

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config": str(config_path.relative_to(REPO_ROOT)),
        "model": generator["model"],
        "decoder": generator["decoder"],
        "strategy": generator["strategy"],
        "target_seconds": target_seconds,
        "tracks": [],
    }

    for track_index, track in enumerate(tracks, start=1):
        track_id = str(track["id"])
        source = project_root / safe_relative(str(track["source"]), ".wav")
        output = project_root / safe_relative(str(track["output"]), ".wav")
        if not source.is_file():
            fail(f"source soundtrack is missing: {source}")
        # Scenario-specific words go first because T5Gemma accepts at most 256 tokens.
        prompt = f"{str(track['prompt']).strip()} {str(generator['prompt_suffix']).strip()}"
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        seed = (
            int(args.seed + track_index - 1)
            if args.seed is not None
            else secrets.randbelow(2**31)
        )
        status = "would-generate" if args.dry_run else "generated"
        print(f"[{track_index}/{len(tracks)}] {track_id} -> {output}", flush=True)
        print(f"  seed={seed} prompt_sha256={prompt_sha256[:12]}", flush=True)

        if output.exists() and not args.overwrite:
            status = "skipped-existing"
        elif not args.dry_run:
            output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f"lpw-{track_id}-output-") as temp_name:
                temp = Path(temp_name)
                reference = temp / "third-part-reference.wav"
                reference_seconds = extract_reference_section(
                    source,
                    reference,
                    float(track["third_part_start_seconds"]),
                )
                generation_seconds = reference_seconds + target_seconds
                raw = temp / "third-part-with-continuation.wav"
                command = [
                    sys.executable,
                    str(ORCHESTRATOR),
                    str(generator["command"]),
                    prompt,
                    "--seconds", str(generation_seconds),
                    "--steps", str(generator["steps"]),
                    "--cfg", str(generator["cfg"]),
                    "--seed", str(seed),
                    "--negative-prompt", str(generator["negative_prompt"]),
                    "--init-audio", str(reference),
                    "--init-noise-level", str(generator["init_noise_level"]),
                    "--inpaint-range", f"{reference_seconds:.3f},{generation_seconds:.3f}",
                    "--output", str(raw),
                    "--overwrite",
                ]
                subprocess.run(command, cwd=REPO_ROOT, check=True)
                generated_only = temp / "generated-continuation-only.wav"
                extract_generated_continuation(
                    raw,
                    generated_only,
                    reference_seconds,
                    target_seconds,
                    float(generator["ending_fade_seconds"]),
                )
                conform_audio(generated_only, output, generator)

        record: dict[str, object] = {
            "id": track_id,
            "source": str(source.relative_to(project_root)),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "path": str(output.relative_to(project_root)),
            "status": status,
            "prompt": prompt,
            "prompt_sha256": prompt_sha256,
            "negative_prompt": generator["negative_prompt"],
            "third_part_start_seconds": track["third_part_start_seconds"],
            "reference_context_seconds": round(
                float(wav_metadata(source)["duration_seconds"])
                - float(track["third_part_start_seconds"]),
                3,
            ),
            "seed": seed,
            "seed_mode": "explicit" if args.seed is not None else "random",
            "init_noise_level": generator["init_noise_level"],
            "cfg": generator["cfg"],
            "reference_included_in_output": False,
            "opening_theme_included": False,
        }
        if output.is_file():
            record["wav"] = wav_metadata(output)
        manifest["tracks"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(tracks)} continuation soundtrack(s) validated.")
        return
    manifest_path = project_root / safe_relative(str(generator["manifest_path"]), ".json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"generation command exited with status {exc.returncode}")
    except KeyboardInterrupt:
        fail("interrupted")
