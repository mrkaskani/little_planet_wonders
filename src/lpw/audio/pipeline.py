from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import PurePosixPath
from typing import Any

from lpw.audio.compiler import (
    compile_dialogue_package,
    resolved_audio_context,
)
from lpw.generation.compiler import compile_wan_shot_package
from lpw.models import DialogueRequest, ShotRequest


def _compile_music_instructions(
    character_id: str | None,
    emotional_tone: str,
    audio: dict[str, Any],
) -> dict[str, Any]:
    tone = emotional_tone.lower()
    theme_id = (
        "danger"
        if any(word in tone for word in ("danger", "tense", "threat"))
        else character_id
    )
    continuity = audio.get("continuity", {}).get("music", {})
    return {
        "cue": continuity.get("active_cue") or theme_id,
        "intensity": continuity.get("intensity", 0.5),
        "continue_from_previous_scene": True,
    }


def _compile_ambience_instructions(
    location_id: str,
    audio: dict[str, Any],
) -> dict[str, Any]:
    continuity = audio.get("continuity", {}).get("ambience", {})
    location_ambience = audio.get("ambience", {}).get("locations", {}).get(
        location_id, {}
    )
    base_asset = location_ambience.get("base_layer", {}).get("asset")
    fallback_environment = (
        PurePosixPath(base_asset).stem if isinstance(base_asset, str) else location_id
    )
    preserve_across_cuts = location_ambience.get("continuity", {}).get(
        "preserve_across_cuts", True
    )
    return {
        "environment": continuity.get("active_environment") or fallback_environment,
        "continue_across_cut": preserve_across_cuts,
    }


def _compile_sound_effects(audio: dict[str, Any]) -> list[dict[str, Any]]:
    active_sounds = audio.get("continuity", {}).get("active_sounds", {})
    return [
        {"id": sound_id.replace("_", "-"), **instructions}
        for sound_id, instructions in active_sounds.items()
        if isinstance(instructions, dict)
    ]


def _compile_mixing_instructions(audio: dict[str, Any]) -> dict[str, Any]:
    audio_rules = audio.get("audio", {})
    mixing = audio.get("mixing", {})
    return {
        "target_lufs": audio_rules.get("dialogue", {}).get(
            "target_lufs",
            mixing.get("loudness", {}).get("web_target_lufs", -16),
        ),
        "music_ducking_db": audio_rules.get("music", {}).get(
            "dialogue_ducking_db",
            mixing.get("music", {}).get("ducking_db", -6),
        ),
    }


def compile_cinematic_shot(
    shot_request: ShotRequest,
    *,
    dialogue_request: DialogueRequest | None = None,
    dialogue_audio_path: str | None = None,
    sound_effects: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the complete, ordered video/audio pipeline plan for one shot."""

    if dialogue_request and dialogue_request.shot_id != shot_request.shot_id:
        raise ValueError("Dialogue and video requests must target the same shot_id.")
    if dialogue_request and dialogue_request.project_id != shot_request.project_id:
        raise ValueError("Dialogue and video requests must target the same project_id.")
    if dialogue_request and not dialogue_audio_path:
        dialogue_audio_path = (
            f"audio/dialogue/{shot_request.shot_id}-{dialogue_request.character_id}.wav"
        )
    if shot_request.shot_type == "dialogue" and dialogue_audio_path:
        shot_request = replace(shot_request, dialogue_audio=dialogue_audio_path)

    video = asdict(compile_wan_shot_package(shot_request))
    dialogue = compile_dialogue_package(dialogue_request) if dialogue_request else None
    if dialogue is not None:
        dialogue["audio_path"] = dialogue_audio_path
    audio = resolved_audio_context(shot_request.project_id)
    character_id = (
        dialogue_request.character_id
        if dialogue_request
        else (shot_request.character_ids[0] if shot_request.character_ids else None)
    )
    return {
        "shot_id": shot_request.shot_id,
        "video": video,
        "dialogue": dialogue,
        "music": _compile_music_instructions(
            character_id, shot_request.emotional_tone, audio
        ),
        "ambience": _compile_ambience_instructions(
            shot_request.location_id, audio
        ),
        "sound_effects": (
            sound_effects if sound_effects is not None else _compile_sound_effects(audio)
        ),
        "mixing": _compile_mixing_instructions(audio),
        "context_hash": video["context_hash"],
    }
