#!/usr/bin/env python3
"""Generate all approved classroom location sounds with Stable Audio 3 Medium."""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "classroom-location-sfx.yaml"
ORCHESTRATOR = REPO_ROOT / "scripts/orchestrator/audio_generator.py"


def fail(message: str) -> "None":
    raise SystemExit(f"error: {message}")


def safe_wav_path(value: str) -> Path:
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts or posix.suffix.lower() != ".wav":
        fail(f"unsafe or non-WAV asset path: {value}")
    return Path(*posix.parts)


def wav_metadata(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        samples = array("h")
        samples.frombytes(audio.readframes(frames))
        if sys.byteorder != "little":
            samples.byteswap()
        peak = max((abs(value) for value in samples), default=0) / 32768.0
        return {
            "channels": audio.getnchannels(),
            "sample_rate_hz": rate,
            "sample_width_bytes": audio.getsampwidth(),
            "frames": frames,
            "duration_seconds": round(frames / rate, 3),
            "peak_dbfs": round(20.0 * math.log10(peak), 2) if peak else None,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }


def apply_peak_ceiling(path: Path, ceiling_dbfs: float) -> bool:
    peak_dbfs = wav_metadata(path)["peak_dbfs"]
    if peak_dbfs is None or float(peak_dbfs) <= ceiling_dbfs:
        return False
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required to apply location-audio peak ceilings")
    temporary = path.with_name(f".{path.stem}.headroom.wav")
    attenuation = ceiling_dbfs - float(peak_dbfs)
    subprocess.run(
        [sox, str(path), str(temporary), "gain", f"{attenuation:.4f}"],
        check=True,
    )
    temporary.replace(path)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate YAML-defined audio for all classroom locations."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--location",
        action="append",
        default=[],
        help="generate only this location ID; may be repeated",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="ASSET_ID_OR_PATH_PREFIX",
        help="generate only matching asset IDs or paths; may be repeated",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--postprocess-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generator = config["generator"]
    output_root = (REPO_ROOT / generator["output_root"]).resolve()

    if generator["model"] != "medium" or generator["decoder"] != "same-l":
        fail("location generation must use Stable Audio 3 Medium with SAME-L")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")

    selected: list[tuple[dict[str, object], dict[str, object], Path, str]] = []
    source_records: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for location in config["locations"]:
        location_id = str(location["id"])
        if args.location and location_id not in args.location:
            continue
        source_path = (REPO_ROOT / str(location["source_profile"])).resolve()
        if not source_path.is_file():
            fail(f"location sound profile is missing: {source_path}")
        source_bytes = source_path.read_bytes()
        source = yaml.safe_load(source_bytes)
        expected_id = str(location["source_profile_id"])
        if source.get("id") != expected_id:
            fail(f"source profile ID mismatch for {location_id}: expected {expected_id}")
        source_records.append(
            {
                "location": location_id,
                "path": str(source_path.relative_to(REPO_ROOT)),
                "id": expected_id,
                "sha256": hashlib.sha256(source_bytes).hexdigest(),
            }
        )
        for asset in location["assets"]:
            relative = safe_wav_path(str(asset["path"]))
            relative_text = relative.as_posix()
            asset_id = str(asset["id"])
            if relative_text in seen_paths:
                fail(f"duplicate output path: {relative_text}")
            seen_paths.add(relative_text)
            if args.only and not any(
                asset_id.startswith(value) or relative_text.startswith(value)
                for value in args.only
            ):
                continue
            selected.append((location, asset, relative, expected_id))

    if not selected:
        fail("no location assets matched the selection")

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config": str(config_path.relative_to(REPO_ROOT)),
        "model": generator["model"],
        "decoder": generator["decoder"],
        "steps": generator["steps"],
        "cfg": generator["cfg"],
        "source_profiles": source_records,
        "assets": [],
    }

    for index, (location, asset, relative, source_id) in enumerate(selected, start=1):
        output = output_root / relative
        location_id = str(location["id"])
        ceiling = float(
            asset.get(
                "peak_ceiling_dbfs", generator["default_peak_ceiling_dbfs"]
            )
        )
        print(f"[{index}/{len(selected)}] {location_id}/{asset['id']}", flush=True)
        status = "would-generate" if args.dry_run else "generated"
        prompt = f"{generator['prompt_prefix']} {asset['prompt']}"
        if output.exists() and not args.overwrite:
            status = "skipped-existing"
            if args.postprocess_existing and not args.dry_run:
                changed = apply_peak_ceiling(output, ceiling)
                status = "postprocessed-existing" if changed else "existing-within-ceiling"
        elif not args.dry_run:
            output.parent.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable,
                str(ORCHESTRATOR),
                str(generator["command"]),
                prompt,
                "--seconds",
                str(asset["seconds"]),
                "--steps",
                str(generator["steps"]),
                "--cfg",
                str(generator["cfg"]),
                "--seed",
                str(asset["seed"]),
                "--output",
                str(output),
            ]
            if args.overwrite:
                command.append("--overwrite")
            subprocess.run(command, cwd=REPO_ROOT, check=True)
            apply_peak_ceiling(output, ceiling)

        record: dict[str, object] = {
            "location": location_id,
            "source_profile_id": source_id,
            "id": asset["id"],
            "path": relative.as_posix(),
            "status": status,
            "prompt": prompt,
            "seconds_requested": asset["seconds"],
            "seed": asset["seed"],
            "peak_ceiling_dbfs": ceiling,
        }
        if output.is_file():
            record["wav"] = wav_metadata(output)
        manifest["assets"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(selected)} location asset(s) validated.")
        return

    manifest_path = (REPO_ROOT / str(generator["manifest_path"])).resolve()
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
