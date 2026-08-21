#!/usr/bin/env python3
"""Generate the named classroom SFX assets from the approved audio spec."""

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


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_LIBRARY = SCRIPT_DIR / "classroom-sfx-library.json"
ORCHESTRATOR = REPO_ROOT / "scripts/orchestrator/audio_generator.py"


def fail(message: str) -> "None":
    raise SystemExit(f"error: {message}")


def safe_relative_path(value: str) -> Path:
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
    """Attenuate only when a generated WAV exceeds its mix-headroom ceiling."""
    metadata = wav_metadata(path)
    peak_dbfs = metadata["peak_dbfs"]
    if peak_dbfs is None or float(peak_dbfs) <= ceiling_dbfs:
        return False
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required to apply the child-safe peak ceiling")
    attenuation_db = ceiling_dbfs - float(peak_dbfs)
    temporary = path.with_name(f".{path.stem}.headroom.wav")
    subprocess.run(
        [sox, str(path), str(temporary), "gain", f"{attenuation_db:.4f}"],
        check=True,
    )
    temporary.replace(path)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate classroom SFX with the local Stable Audio 3 Medium model."
    )
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="PATH_OR_PREFIX",
        help="generate only matching asset paths; may be repeated",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--postprocess-existing",
        action="store_true",
        help="apply configured peak ceilings to matching existing assets",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    library_path = args.library.resolve()
    data = json.loads(library_path.read_text(encoding="utf-8"))

    spec_path = (REPO_ROOT / data["spec"]).resolve()
    principles_path = (REPO_ROOT / data["principles"]).resolve()
    output_root = (REPO_ROOT / data["output_root"]).resolve()
    if not spec_path.is_file() or not principles_path.is_file():
        fail("sound-effect specification files are missing")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")

    spec_text = spec_path.read_text(encoding="utf-8")
    selected: list[dict[str, object]] = []
    for asset in data["assets"]:
        relative = safe_relative_path(str(asset["path"]))
        if str(relative.as_posix()) not in spec_text:
            fail(f"asset is not declared by sound-effects.yaml: {relative.as_posix()}")
        if args.only and not any(relative.as_posix().startswith(value) for value in args.only):
            continue
        selected.append(asset)

    if not selected:
        fail("no assets matched the selection")

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_library": str(library_path.relative_to(REPO_ROOT)),
        "spec": data["spec"],
        "principles": data["principles"],
        "model": data["model"],
        "decoder": data["decoder"],
        "assets": [],
    }

    for index, asset in enumerate(selected, start=1):
        relative = safe_relative_path(str(asset["path"]))
        output = output_root / relative
        status = "would-generate" if args.dry_run else "generated"
        print(f"[{index}/{len(selected)}] {relative.as_posix()}", flush=True)
        if output.exists() and not args.overwrite:
            status = "skipped-existing"
            if args.postprocess_existing and not args.dry_run:
                ceiling = float(asset.get("peak_ceiling_dbfs", data["peak_ceiling_dbfs"]))
                changed = apply_peak_ceiling(output, ceiling)
                status = "postprocessed-existing" if changed else "existing-within-ceiling"
        elif not args.dry_run:
            output.parent.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable,
                str(ORCHESTRATOR),
                str(data["generator_kind"]),
                str(asset["prompt"]),
                "--seconds",
                str(asset["seconds"]),
                "--steps",
                str(data["steps"]),
                "--cfg",
                str(data["cfg"]),
                "--seed",
                str(asset["seed"]),
                "--output",
                str(output),
            ]
            if data.get("negative_prompt"):
                command += ["--negative-prompt", str(data["negative_prompt"])]
            if args.overwrite:
                command.append("--overwrite")
            subprocess.run(command, cwd=REPO_ROOT, check=True)
            ceiling = float(asset.get("peak_ceiling_dbfs", data["peak_ceiling_dbfs"]))
            apply_peak_ceiling(output, ceiling)

        record = {
            "path": relative.as_posix(),
            "status": status,
            "prompt": asset["prompt"],
            "negative_prompt": data["negative_prompt"],
            "seconds_requested": asset["seconds"],
            "steps": data["steps"],
            "cfg": data["cfg"],
            "seed": asset["seed"],
            "peak_ceiling_dbfs": asset.get(
                "peak_ceiling_dbfs", data["peak_ceiling_dbfs"]
            ),
        }
        if output.is_file():
            record["wav"] = wav_metadata(output)
        manifest["assets"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(selected)} asset(s) validated.")
        return

    manifest_path = (REPO_ROOT / str(data["manifest_path"])).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"generation command exited with status {exc.returncode}")
