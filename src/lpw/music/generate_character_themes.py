#!/usr/bin/env python3
"""Render locked character leitmotifs and reference-conditioned arrangements."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import numpy as np
import yaml
from scipy.io import wavfile


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CONFIG = (
    REPO_ROOT / "scripts/stable-audio-3-medium/character-theme-music.yaml"
)
ORCHESTRATOR = REPO_ROOT / "scripts/orchestrator/audio_generator.py"
NOTE_PATTERN = re.compile(r"^([A-G])(#|b)?(-?\d+)$")
SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def fail(message: str) -> "None":
    raise SystemExit(f"error: {message}")


def safe_relative_wav(value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() != ".wav":
        fail(f"unsafe or non-WAV profile asset path: {value}")
    return Path(*path.parts)


def note_frequency(note: str) -> float:
    match = NOTE_PATTERN.match(note)
    if not match:
        fail(f"unsupported canonical motif note: {note}")
    letter, accidental, octave_text = match.groups()
    semitone = SEMITONES[letter] + (1 if accidental == "#" else -1 if accidental == "b" else 0)
    midi = (int(octave_text) + 1) * 12 + semitone
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def envelope(t: np.ndarray, attack: float, release_at: float, decay: float) -> np.ndarray:
    attack_curve = np.minimum(t / max(attack, 0.001), 1.0)
    natural_decay = np.exp(-t / decay)
    release = np.ones_like(t)
    tail = t > release_at
    release[tail] = np.exp(-(t[tail] - release_at) / 0.12)
    return attack_curve * natural_decay * release


def synth_note(instrument: str, frequency: float, duration: float, rate: int, rng: np.random.Generator) -> np.ndarray:
    tail = 0.42 if instrument == "felt-piano" else 0.20
    t = np.arange(int((duration + tail) * rate), dtype=np.float64) / rate
    if instrument == "felt-piano":
        partials = ((1.0, 1.0), (2.0, 0.22), (3.0, 0.07), (4.02, 0.025))
        tone = sum(
            amplitude * np.sin(2.0 * np.pi * frequency * multiple * t + 0.15 * multiple)
            for multiple, amplitude in partials
        )
        tone += 0.18 * np.sin(2.0 * np.pi * frequency * 0.5 * t)
        tone *= envelope(t, 0.022, duration, 1.20)
        hammer = rng.normal(0.0, 1.0, len(t)) * np.exp(-t / 0.018) * 0.018
        return tone + hammer

    if instrument != "celesta":
        fail(f"unsupported signature instrument for motif rendering: {instrument}")
    partials = ((1.0, 0.72), (2.01, 1.0), (3.98, 0.31), (5.41, 0.18), (6.78, 0.08))
    bell = sum(
        amplitude * np.sin(2.0 * np.pi * frequency * multiple * t + 0.23 * multiple)
        for multiple, amplitude in partials
    )
    wooden = 0.28 * np.sin(2.0 * np.pi * frequency * t) + 0.08 * np.sin(
        2.0 * np.pi * frequency * 4.0 * t
    )
    sound = bell * envelope(t, 0.003, duration * 0.70, 0.38)
    sound += wooden * envelope(t, 0.002, duration * 0.62, 0.22)
    return sound


def render_leitmotif(
    character: str,
    instrument: str,
    notes: list[str],
    durations: list[float],
    onsets: list[float],
    seed: int,
    output: Path,
) -> None:
    if not notes or not (len(notes) == len(durations) == len(onsets)):
        fail(f"{character} canonical notes, durations, and onsets must be equal non-empty lists")
    rate = 48000
    tail = 0.58 if instrument == "felt-piano" else 0.30
    total = max(onset + duration for onset, duration in zip(onsets, durations, strict=True)) + tail
    mono = np.zeros(int(total * rate), dtype=np.float64)
    rng = np.random.default_rng(seed)
    for note, duration, onset in zip(notes, durations, onsets, strict=True):
        cursor = int(onset * rate)
        rendered = synth_note(instrument, note_frequency(note), duration, rate, rng)
        end = min(cursor + len(rendered), len(mono))
        mono[cursor:end] += rendered[: end - cursor]

    # A tiny warm room makes the guide musical while keeping every note readable.
    room = mono.copy()
    for delay_seconds, level in ((0.047, 0.12), (0.083, 0.07), (0.131, 0.035)):
        delay = int(delay_seconds * rate)
        room[delay:] += mono[:-delay] * level
    peak = float(np.max(np.abs(room)))
    if peak:
        room *= 0.72 / peak
    stereo = np.column_stack((room, np.roll(room, 29) * 0.98)).astype(np.float32)

    output.parent.mkdir(parents=True, exist_ok=True)
    raw = output.with_name(f".{output.stem}.motif-float.wav")
    wavfile.write(raw, rate, stereo)
    try:
        conform_audio(raw, output, 48000, 24, 2, -1.0)
    finally:
        raw.unlink(missing_ok=True)


def wav_metadata(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        return {
            "channels": audio.getnchannels(),
            "sample_rate_hz": audio.getframerate(),
            "sample_width_bytes": audio.getsampwidth(),
            "frames": audio.getnframes(),
            "duration_seconds": round(audio.getnframes() / audio.getframerate(), 3),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }


def conform_audio(source: Path, output: Path, rate: int, bits: int, channels: int, ceiling: float) -> None:
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required for character music generation")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sox,
            str(source),
            "-r", str(rate),
            "-b", str(bits),
            "-c", str(channels),
            str(output),
            "gain", "-3",
            "rate", "-v", str(rate),
            "gain", "-n", str(ceiling),
        ],
        check=True,
    )


def make_context_audio(source: Path, output: Path) -> None:
    sox = shutil.which("sox")
    if not sox:
        fail("SoX is required to create Stable Audio context WAVs")
    subprocess.run(
        [sox, str(source), "-r", "44100", "-b", "16", "-c", "2", str(output), "rate", "-v", "44100"],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render canonical motifs, then generate arrangements from motif audio context."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--character", action="append", default=[])
    parser.add_argument("--stage", action="append", choices=("motif", "arrangement"), default=[])
    parser.add_argument("--arrangement", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    generator = config["generator"]
    if generator["model"] != "medium" or generator["decoder"] != "same-l":
        fail("arrangements must use Stable Audio 3 Medium with SAME-L")
    if not ORCHESTRATOR.is_file():
        fail(f"audio orchestrator is missing: {ORCHESTRATOR}")

    stages = set(args.stage or ("motif", "arrangement"))
    project_root = (REPO_ROOT / str(generator["project_root"])).resolve()
    profile_glob = PurePosixPath(str(generator["profile_glob"]))
    if profile_glob.is_absolute() or ".." in profile_glob.parts:
        fail(f"unsafe character music profile glob: {profile_glob}")
    profile_jobs: list[dict[str, object]] = []
    for profile_path in sorted(project_root.glob(profile_glob.as_posix())):
        profile_bytes = profile_path.read_bytes()
        document = yaml.safe_load(profile_bytes)
        profile = document.get("music_profile") if isinstance(document, dict) else None
        if not isinstance(profile, dict):
            fail(f"music_profile root is missing: {profile_path}")
        character_data = profile.get("character")
        if not isinstance(character_data, dict) or not character_data.get("id"):
            fail(f"music_profile.character.id is missing: {profile_path}")
        character = str(character_data["id"])
        if profile_path.parent.name != character:
            fail(f"profile directory and character ID differ: {profile_path}")
        if args.character and character not in args.character:
            continue
        profile_jobs.append(
            {
                "character": character,
                "path": profile_path,
                "bytes": profile_bytes,
                "profile": profile,
            }
        )
    if not profile_jobs:
        fail("no characters matched the selection")

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config": str(config_path.relative_to(REPO_ROOT)),
        "pipeline": "locked-leitmotif-to-reference-conditioned-arrangement",
        "model": generator["model"],
        "decoder": generator["decoder"],
        "profile_glob": profile_glob.as_posix(),
        "assets": [],
    }

    for job in profile_jobs:
        character = str(job["character"])
        profile_path = Path(job["path"])
        profile_bytes = bytes(job["bytes"])
        profile = job["profile"]
        if not isinstance(profile, dict):
            fail(f"invalid cached music profile for {character}")
        generation_profile = profile.get("leitmotif_generation_profile")
        if not isinstance(generation_profile, dict):
            fail(f"{character} profile has no leitmotif_generation_profile")
        for required in (
            "id",
            "motif_seed",
            "cfg",
            "init_noise_level",
            "motif_preservation_mode",
            "identity_prompt",
            "identity_negative_prompt",
        ):
            if required not in generation_profile:
                fail(f"{character} leitmotif_generation_profile.{required} is missing")
        motif = profile["leitmotif"]
        character_basis = motif.get("character_basis")
        if not isinstance(character_basis, dict):
            fail(f"{character} leitmotif.character_basis is missing")
        source_records: dict[str, object] = {
            "traits": character_basis.get("traits"),
            "musical_translation": character_basis.get("musical_translation"),
        }
        for source_key in ("character_profile", "voice_profile"):
            source_relative = PurePosixPath(str(character_basis.get(source_key, "")))
            if source_relative.is_absolute() or ".." in source_relative.parts:
                fail(f"unsafe {character} leitmotif character source: {source_relative}")
            source_path = project_root / Path(*source_relative.parts)
            if not source_path.is_file():
                fail(f"{character} leitmotif character source is missing: {source_path}")
            source_records[source_key] = {
                "path": source_relative.as_posix(),
                "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
            }
        notes = motif["optional_note_example"]["notes"]
        durations = motif["canonical_note_durations_seconds"]
        onsets = motif["canonical_note_onsets_seconds"]
        motif_phrase_end = max(
            float(onset) + float(duration)
            for onset, duration in zip(onsets, durations, strict=True)
        )
        signature_instrument = profile["instrumentation"]["signature_instrument"]["name"]
        if not (len(notes) == len(durations) == len(onsets) == int(motif["note_count"])):
            fail(f"{character} canonical note count does not match leitmotif.note_count")
        paths = profile["asset_paths"]
        defaults = profile["technical_defaults"]
        channels = 2 if defaults["channels"] == "stereo" else 1
        motif_relative = safe_relative_wav(str(paths["leitmotif"]))
        motif_output = project_root / motif_relative

        if "motif" in stages:
            status = "would-render" if args.dry_run else "rendered"
            print(f"[{character}] locked leitmotif -> {motif_output}", flush=True)
            if motif_output.exists() and not args.overwrite:
                status = "skipped-existing"
            elif not args.dry_run:
                render_leitmotif(
                    character,
                    signature_instrument,
                    notes,
                    durations,
                    onsets,
                    int(generation_profile["motif_seed"]),
                    motif_output,
                )
            record: dict[str, object] = {
                "character": character,
                "kind": "canonical-leitmotif",
                "profile_id": profile["id"],
                "motif_id": motif["id"],
                "motif_revision": motif["revision"],
                "character_basis": source_records,
                "path": motif_relative.as_posix(),
                "notes": notes,
                "note_durations_seconds": durations,
                "note_onsets_seconds": onsets,
                "signature_instrument": signature_instrument,
                "generation_profile_id": generation_profile["id"],
                "seed": generation_profile["motif_seed"],
                "status": status,
            }
            if motif_output.is_file():
                record["wav"] = wav_metadata(motif_output)
            manifest["assets"].append(record)

        if "arrangement" not in stages:
            continue
        if not motif_output.is_file() and not args.dry_run:
            fail(f"canonical motif must exist before arranging: {motif_output}")

        samples = profile.get("leitmotif_samples")
        if not isinstance(samples, list) or not samples:
            fail(f"{character} profile has no leitmotif_samples")
        for arrangement in samples:
            arrangement_id = str(arrangement["id"])
            if args.arrangement and arrangement_id not in args.arrangement:
                continue
            prompt_key = str(arrangement["prompt"])
            asset_key = str(arrangement["asset"])
            if prompt_key not in profile["generation_prompts"] or asset_key not in paths:
                fail(f"{character}/{arrangement_id} is missing its profile prompt or asset path")
            relative = safe_relative_wav(str(paths[asset_key]))
            output = project_root / relative
            cfg = float(arrangement.get("cfg", generation_profile["cfg"]))
            init_noise_level = float(
                arrangement.get("init_noise_level", generation_profile["init_noise_level"])
            )
            prompt = (
                f"{str(generation_profile['identity_prompt']).strip()} "
                f"Target feeling: {arrangement['feeling']}. "
                f"Target emotion: {arrangement['emotion']}. "
                f"{str(profile['generation_prompts'][prompt_key]).strip()} "
                "The opening audio is the character's locked canonical leitmotif. Keep that complete opening "
                "melody unchanged, then continue and answer it in the requested emotional arrangement. Reuse "
                "recognizable fragments of its exact note order, rhythm, and contour in the generated continuation. "
                f"{str(generator['prompt_suffix']).strip()}"
            )
            negative = " ".join(
                (
                    str(generation_profile["identity_negative_prompt"]).strip(),
                    str(profile["generation_prompts"].get("negative_prompt", "")).strip(),
                )
            )
            status = "would-generate" if args.dry_run else "generated"
            print(f"[{character}] {arrangement_id} from leitmotif context -> {output}", flush=True)
            if output.exists() and not args.overwrite:
                status = "skipped-existing"
            elif not args.dry_run:
                if generation_profile["motif_preservation_mode"] != "inpaint-after-canonical-motif":
                    fail(
                        f"unsupported motif preservation mode for {character}: "
                        f"{generation_profile['motif_preservation_mode']}"
                    )
                arrangement_seconds = float(arrangement["seconds"])
                if motif_phrase_end >= arrangement_seconds:
                    fail(f"{character}/{arrangement_id} is too short for its canonical motif")
                output.parent.mkdir(parents=True, exist_ok=True)
                context = output.with_name(f".{output.stem}.motif-context.wav")
                raw = output.with_name(f".{output.stem}.stable-audio-3.wav")
                try:
                    make_context_audio(motif_output, context)
                    command = [
                        sys.executable, str(ORCHESTRATOR), str(generator["command"]), prompt,
                        "--seconds", str(arrangement["seconds"]),
                        "--steps", str(generator["steps"]),
                        "--cfg", str(cfg),
                        "--seed", str(arrangement["seed"]),
                        "--negative-prompt", negative,
                        "--init-audio", str(context),
                        "--init-noise-level", str(init_noise_level),
                        "--inpaint-range", f"{motif_phrase_end:.3f},{arrangement_seconds:.3f}",
                        "--output", str(raw), "--overwrite",
                    ]
                    subprocess.run(command, cwd=REPO_ROOT, check=True)
                    conform_audio(
                        raw, output, int(defaults["sample_rate"]), int(defaults["bit_depth"]),
                        channels, float(generator["peak_ceiling_dbfs"]),
                    )
                finally:
                    context.unlink(missing_ok=True)
                    raw.unlink(missing_ok=True)
            record = {
                "character": character,
                "kind": "leitmotif-conditioned-arrangement",
                "arrangement": arrangement_id,
                "feeling": arrangement["feeling"],
                "emotion": arrangement["emotion"],
                "generation_profile_id": generation_profile["id"],
                "motif_preservation_mode": generation_profile["motif_preservation_mode"],
                "preserved_motif_seconds": round(motif_phrase_end, 3),
                "profile_id": profile["id"],
                "motif_id": motif["id"],
                "motif_revision": motif["revision"],
                "character_basis": source_records,
                "motif_path": motif_relative.as_posix(),
                "path": relative.as_posix(),
                "prompt_key": prompt_key,
                "prompt": prompt,
                "seed": arrangement["seed"],
                "cfg": cfg,
                "init_noise_level": init_noise_level,
                "status": status,
            }
            if output.is_file():
                record["wav"] = wav_metadata(output)
            manifest["assets"].append(record)

    if args.dry_run:
        print(f"Dry run complete: {len(manifest['assets'])} asset(s) validated.")
        return
    manifest_path = (REPO_ROOT / str(generator["manifest_path"])).resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["source_profiles"] = [
        {
            "character": str(job["character"]),
            "path": str(Path(job["path"]).relative_to(REPO_ROOT)),
            "profile_id": job["profile"]["id"],
            "sha256": hashlib.sha256(bytes(job["bytes"])).hexdigest(),
        }
        for job in profile_jobs
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"generation command exited with status {exc.returncode}")
    except KeyboardInterrupt:
        fail("interrupted")
