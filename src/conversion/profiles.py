"""Resolve locked clone references from character voice profiles."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class LockedVoiceReference:
    """A profile-backed audio reference and its exact transcript."""

    character: str
    profile_path: Path
    audio_path: Path
    text: str
    sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_locked_voice(
    workspace_root: Path,
    project: str,
    character: str,
) -> LockedVoiceReference:
    """Resolve a character's neutral-friendly reference from its profile."""

    project_root = (
        workspace_root
        / "src/lpw/context/projects"
        / project
    ).resolve()
    profile_path = project_root / "characters" / character / "voice-profile.yaml"
    if not profile_path.is_file():
        raise FileNotFoundError(f"voice profile not found for {character}: {profile_path}")
    payload = yaml.safe_load(profile_path.read_text())
    try:
        neutral = payload["references"]["neutral-friendly"]
        relative_audio = str(neutral["path"])
        reference_text = str(neutral["text"]).strip()
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"voice profile lacks a structured neutral-friendly reference: {profile_path}"
        ) from exc
    audio_path = (project_root / relative_audio).resolve()
    if not audio_path.is_relative_to(project_root):
        raise ValueError(f"voice reference escapes project context: {audio_path}")
    if not audio_path.is_file():
        raise FileNotFoundError(f"locked voice reference is missing: {audio_path}")
    if not reference_text:
        raise ValueError(f"neutral reference transcript is empty: {profile_path}")
    return LockedVoiceReference(
        character=character,
        profile_path=profile_path,
        audio_path=audio_path,
        text=reference_text,
        sha256=_sha256(audio_path),
    )
