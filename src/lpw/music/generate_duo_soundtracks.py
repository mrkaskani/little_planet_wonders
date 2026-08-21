#!/usr/bin/env python3
"""Generate profile-driven Riri/Yoyo soundtrack samples with Stable Audio 3."""

from __future__ import annotations

import argparse
import hashlib
import json
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
    REPO_ROOT / "src/lpw/context/projects/riri-yoyo/audios/soundtrack-samples.yaml"
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


def conform_audio(source: Path, output: Path, generator: dict[str, object]) -> None:
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required for soundtrack generation")
    channels = 2 if generator["channels"] == "stereo" else 1
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sox,
            str(source),
            "-r", str(generator["sample_rate"]),
            "-b", str(generator["bit_depth"]),
            "-c", str(channels),
            str(output),
            "gain", "-3",
            "rate", "-v", str(generator["sample_rate"]),
            "gain", "-n", str(generator["peak_ceiling_dbfs"]),
        ],
        check=True,
    )


def build_duo_context(motifs: list[Path], gap_seconds: float, directory: Path) -> tuple[Path, float]:
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required to build the dual-motif context")
    converted: list[Path] = []
    for index, motif in enumerate(motifs, start=1):
        target = directory / f"motif-{index}.wav"
        subprocess.run(
            [sox, str(motif), "-r", "44100", "-b", "16", "-c", "2", str(target), "rate", "-v", "44100"],
            check=True,
        )
        converted.append(target)
    silence = directory / "gap.wav"
    subprocess.run(
        [sox, "-n", "-r", "44100", "-b", "16", "-c", "2", str(silence), "trim", "0", str(gap_seconds)],
        check=True,
    )
    context = directory / "riri-yoyo-motif-context.wav"
    inputs: list[str] = []
    for index, motif in enumerate(converted):
        if index:
            inputs.append(str(silence))
        inputs.append(str(motif))
    subprocess.run([sox, *inputs, str(context)], check=True)
    with wave.open(str(context), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
    return context, duration


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dual-character soundtrack samples from profile motifs."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--track", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generator = config["generator"]
    if generator["model"] != "medium" or generator["decoder"] != "same-l":
        fail("duo soundtracks must use Stable Audio 3 Medium with SAME-L")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")

    project_root = (REPO_ROOT / safe_relative(str(generator["project_root"]))).resolve()
    output_root = (project_root / safe_relative(str(generator["output_root"]))).resolve()
    motif_paths: list[Path] = []
    profile_records: list[dict[str, object]] = []
    motif_records: list[dict[str, object]] = []
    for character in config["characters"]:
        profile_path = project_root / safe_relative(str(character["profile"]), ".yaml")
        profile_bytes = profile_path.read_bytes()
        profile = yaml.safe_load(profile_bytes).get("music_profile")
        character_id = str(character["id"])
        if not isinstance(profile, dict) or profile.get("character", {}).get("id") != character_id:
            fail(f"music profile character mismatch: {profile_path}")
        motif_key = str(character["motif_asset"])
        motif_path = project_root / safe_relative(str(profile["asset_paths"][motif_key]), ".wav")
        if not motif_path.is_file():
            fail(f"canonical motif is missing: {motif_path}")
        motif_paths.append(motif_path)
        profile_records.append(
            {
                "character": character_id,
                "path": str(profile_path.relative_to(REPO_ROOT)),
                "profile_id": profile["id"],
                "sha256": hashlib.sha256(profile_bytes).hexdigest(),
            }
        )
        motif_records.append(
            {
                "character": character_id,
                "path": str(motif_path.relative_to(project_root)),
                "motif_id": profile["leitmotif"]["id"],
                "revision": profile["leitmotif"]["revision"],
                "notes": profile["leitmotif"]["optional_note_example"]["notes"],
                "wav": wav_metadata(motif_path),
            }
        )

    tracks = [
        track for track in config["soundtracks"]
        if not args.track or track["id"] in args.track
    ]
    if not tracks:
        fail("no soundtrack samples matched the selection")

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config": str(config_path.relative_to(REPO_ROOT)),
        "model": generator["model"],
        "decoder": generator["decoder"],
        "source_profiles": profile_records,
        "source_motifs": motif_records,
        "soundtracks": [],
    }

    with tempfile.TemporaryDirectory(prefix="lpw-duo-soundtracks-") as temp_name:
        context: Path | None = None
        context_seconds = sum(float(item["wav"]["duration_seconds"]) for item in motif_records)
        context_seconds += float(generator["motif_gap_seconds"]) * (len(motif_records) - 1)
        for index, track in enumerate(tracks, start=1):
            relative = safe_relative(str(track["path"]), ".wav")
            output = output_root / relative
            prompt = f"{str(generator['prompt_prefix']).strip()} {str(track['prompt']).strip()}"
            status = "would-generate" if args.dry_run else "generated"
            print(f"[{index}/{len(tracks)}] {track['id']} -> {output}", flush=True)
            if output.exists() and not args.overwrite:
                status = "skipped-existing"
            elif not args.dry_run:
                if context is None:
                    context, context_seconds = build_duo_context(
                        motif_paths,
                        float(generator["motif_gap_seconds"]),
                        Path(temp_name),
                    )
                seconds = float(track["seconds"])
                if context_seconds >= seconds:
                    fail(f"track is shorter than its dual-motif context: {track['id']}")
                raw = Path(temp_name) / f"{track['id']}.raw.wav"
                command = [
                    sys.executable, str(ORCHESTRATOR), str(generator["command"]), prompt,
                    "--seconds", str(seconds),
                    "--steps", str(generator["steps"]),
                    "--cfg", str(generator["cfg"]),
                    "--seed", str(track["seed"]),
                    "--negative-prompt", str(generator["negative_prompt"]),
                    "--init-audio", str(context),
                    "--init-noise-level", str(generator["init_noise_level"]),
                    "--inpaint-range", f"{context_seconds:.3f},{seconds:.3f}",
                    "--output", str(raw), "--overwrite",
                ]
                subprocess.run(command, cwd=REPO_ROOT, check=True)
                conform_audio(raw, output, generator)

            record: dict[str, object] = {
                "id": track["id"],
                "feeling": track["feeling"],
                "path": str(output.relative_to(project_root)),
                "status": status,
                "seconds_requested": track["seconds"],
                "seed": track["seed"],
                "prompt": prompt,
                "negative_prompt": generator["negative_prompt"],
                "preserved_dual_motif_seconds": round(context_seconds, 3),
            }
            if output.is_file():
                record["wav"] = wav_metadata(output)
            manifest["soundtracks"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(tracks)} soundtrack sample(s) validated.")
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
