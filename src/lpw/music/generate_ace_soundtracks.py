#!/usr/bin/env python3
"""Generate profile-driven Riri/Yoyo soundtracks with ACE-Step 1.5."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CONFIG = (
    REPO_ROOT / "src/lpw/context/projects/riri-yoyo/audios/ace-soundtracks.yaml"
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


def compact(value: object) -> str:
    return " ".join(str(value).split())


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


def load_profiles(
    project_root: Path,
    characters: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, object]]]:
    profiles: dict[str, dict[str, Any]] = {}
    records: list[dict[str, object]] = []
    for character in characters:
        character_id = str(character["id"])
        profile_path = project_root / safe_relative(str(character["profile"]), ".yaml")
        if not profile_path.is_file():
            fail(f"character music profile is missing: {profile_path}")
        profile_bytes = profile_path.read_bytes()
        document = yaml.safe_load(profile_bytes)
        profile = document.get("music_profile") if isinstance(document, dict) else None
        if not isinstance(profile, dict):
            fail(f"music_profile is missing: {profile_path}")
        if profile.get("character", {}).get("id") != character_id:
            fail(f"music profile character mismatch: {profile_path}")
        for key in (
            "musical_identity",
            "leitmotif",
            "leitmotif_generation_profile",
            "generation_prompts",
        ):
            if not isinstance(profile.get(key), dict):
                fail(f"{character_id} music profile is missing {key}")
        profiles[character_id] = profile
        records.append(
            {
                "character": character_id,
                "profile_id": profile["id"],
                "path": str(profile_path.relative_to(REPO_ROOT)),
                "sha256": hashlib.sha256(profile_bytes).hexdigest(),
            }
        )
    return profiles, records


def profile_prompt(profile: dict[str, Any], prompt_key: str) -> str:
    character = profile["character"]
    identity = profile["musical_identity"]
    motif = profile["leitmotif"]
    generation = profile["leitmotif_generation_profile"]
    prompts = profile["generation_prompts"]
    if prompt_key not in prompts:
        fail(f"{profile['id']} does not define generation prompt {prompt_key!r}")
    notes = ", ".join(str(note) for note in motif["optional_note_example"]["notes"])
    durations = ", ".join(
        f"{float(value):g}s" for value in motif["canonical_note_durations_seconds"]
    )
    return compact(
        f"{character['name']} identity from {profile['id']}: "
        f"{identity['summary']} "
        f"Canonical motif notes in exact order: {notes}. "
        f"Canonical note durations in exact order: {durations}. "
        f"Rhythmic identity: {motif['rhythm']['pattern_description']} "
        f"Register: {motif['register']['range']}. "
        f"Production identity: {generation['identity_prompt']} "
        f"Scenario arrangement from the character profile: {prompts[prompt_key]}"
    )


def build_prompt(
    track: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    character_order: list[str],
    suffix: str,
) -> str:
    prompt_key = str(track["profile_prompt_key"])
    identities = " ".join(
        profile_prompt(profiles[character_id], prompt_key)
        for character_id in character_order
    )
    return compact(
        f"Instrumental preschool animation soundtrack. Scenario: {track['scenario']} "
        f"Target tempo: {track['bpm']} BPM. Time signature: {track['time_signature']}. "
        f"{identities} {suffix}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate character-profile-driven soundtracks with ACE-Step 1.5."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--track", action="append", default=[])
    parser.add_argument("--seed", type=int, help="reproducible base seed")
    parser.add_argument("--server-url")
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generator = config["generator"]
    if generator["engine"] != "ace-step-1.5":
        fail("ACE soundtrack config must use ace-step-1.5")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")

    project_root = (REPO_ROOT / safe_relative(str(generator["project_root"]))).resolve()
    output_root = project_root / safe_relative(str(generator["output_root"]))
    profiles, profile_records = load_profiles(project_root, config["characters"])
    character_order = [str(item["id"]) for item in config["characters"]]
    tracks = [
        track
        for track in config["soundtracks"]
        if not args.track or track["id"] in args.track
    ]
    if not tracks:
        fail("no ACE soundtrack matched the selection")

    server_url = str(args.server_url or generator["server_url"])
    timeout = float(args.timeout or generator["timeout_seconds"])
    manifest_path = project_root / safe_relative(
        str(generator["manifest_path"]), ".json"
    )
    previous_records: dict[str, dict[str, object]] = {}
    if args.track and manifest_path.is_file():
        try:
            previous_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if previous_manifest.get("source_config") == str(
                config_path.relative_to(REPO_ROOT)
            ):
                previous_records = {
                    str(record["id"]): record
                    for record in previous_manifest.get("soundtracks", [])
                    if isinstance(record, dict) and "id" in record
                }
        except (json.JSONDecodeError, OSError):
            previous_records = {}
    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config": str(config_path.relative_to(REPO_ROOT)),
        "engine": generator["engine"],
        "model": generator["model"],
        "lm_model": generator["lm_model"],
        "source_profiles": profile_records,
        "soundtracks": [],
    }

    for index, track in enumerate(tracks, start=1):
        track_id = str(track["id"])
        output = output_root / safe_relative(str(track["output"]), ".wav")
        reference_audio = project_root / safe_relative(
            str(track["reference_audio"]), ".wav"
        )
        if not reference_audio.is_file():
            fail(f"soundtrack reference audio is missing: {reference_audio}")
        prompt = build_prompt(
            track,
            profiles,
            character_order,
            str(generator["prompt_suffix"]),
        )
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        seed = (
            int(args.seed + index - 1)
            if args.seed is not None
            else secrets.randbelow(2**31)
        )
        status = "would-generate" if args.dry_run else "generated"
        print(f"[{index}/{len(tracks)}] {track_id} -> {output}", flush=True)
        print(f"  seed={seed} prompt_sha256={prompt_sha256[:12]}", flush=True)

        if output.exists() and not args.overwrite:
            status = "verified-existing"
        elif not args.dry_run:
            output.parent.mkdir(parents=True, exist_ok=True)
            command = [
                sys.executable,
                str(ORCHESTRATOR),
                "song",
                prompt,
                "--lyrics", "[Instrumental]",
                "--seconds", str(track["seconds"]),
                "--steps", str(generator["steps"]),
                "--seed", str(seed),
                "--format", "wav",
                "--no-thinking",
                "--source-audio", str(reference_audio),
                "--task-type", "cover",
                "--audio-cover-strength", str(generator["audio_cover_strength"]),
                "--cover-noise-strength", str(generator["cover_noise_strength"]),
                "--server-url", server_url,
                "--timeout", str(timeout),
                "--output", str(output),
            ]
            if args.overwrite:
                command.append("--overwrite")
            subprocess.run(command, cwd=REPO_ROOT, check=True)

        record: dict[str, object] = {
            "id": track_id,
            "path": str(output.relative_to(project_root)),
            "status": status,
            "seconds_requested": track["seconds"],
            "bpm": track["bpm"],
            "time_signature": track["time_signature"],
            "profile_prompt_key": track["profile_prompt_key"],
            "seed": seed,
            "seed_mode": "explicit" if args.seed is not None else "random",
            "prompt": prompt,
            "prompt_sha256": prompt_sha256,
            "instrumental": True,
            "reference_audio": {
                "path": str(reference_audio.relative_to(project_root)),
                "sha256": hashlib.sha256(reference_audio.read_bytes()).hexdigest(),
                "task_type": "cover",
                "audio_cover_strength": generator["audio_cover_strength"],
                "cover_noise_strength": generator["cover_noise_strength"],
            },
        }
        if output.is_file():
            record["wav"] = wav_metadata(output)
        manifest["soundtracks"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(tracks)} ACE soundtrack(s) validated.")
        return
    if args.track and previous_records:
        current_records = {
            str(record["id"]): record for record in manifest["soundtracks"]
        }
        previous_records.update(current_records)
        manifest["soundtracks"] = [
            previous_records[str(track["id"])]
            for track in config["soundtracks"]
            if str(track["id"]) in previous_records
        ]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"ACE generation command exited with status {exc.returncode}")
    except KeyboardInterrupt:
        fail("interrupted")
