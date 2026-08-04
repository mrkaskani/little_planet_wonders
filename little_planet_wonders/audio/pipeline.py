from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from little_planet_wonders.audio.compiler import (
    compile_dialogue_package,
    resolved_audio_context,
)
from little_planet_wonders.context.loader import load_project_context
from little_planet_wonders.generation.compiler import compile_wan_shot_package
from little_planet_wonders.models import DialogueRequest, ShotRequest


def _select_music_cue(
    character_id: str | None, emotional_tone: str, music: dict[str, Any]
) -> dict[str, Any]:
    tone = emotional_tone.lower()
    theme_id = "danger" if any(word in tone for word in ("danger", "tense", "threat")) else character_id
    theme = music.get("themes", {}).get(theme_id or "", {})
    return {
        "theme": theme_id,
        "motif": theme.get("motif"),
        "instruments": theme.get("instruments", []),
        "tempo_bpm": theme.get("tempo_bpm", music.get("tempo", {}).get("default_bpm")),
        "continue_from_previous_scene": True,
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
    context = load_project_context(
        shot_request.project_id,
        character_ids=shot_request.character_ids,
        location_id=shot_request.location_id,
    )
    audio = resolved_audio_context(shot_request.project_id)
    location = context.get("location") or {}
    environment = location.get("environment", {})
    character_id = dialogue_request.character_id if dialogue_request else (
        shot_request.character_ids[0] if shot_request.character_ids else None
    )
    return {
        "shot_id": shot_request.shot_id,
        "video": video,
        "dialogue": dialogue,
        "music": _select_music_cue(character_id, shot_request.emotional_tone, audio["music"]),
        "ambience": {
            "location_id": shot_request.location_id,
            "environment": environment,
            "continue_across_cut": True,
            "rules": audio["ambience"],
        },
        "sound_effects": sound_effects or [],
        "mixing": audio["mixing"],
        "context_hash": video["context_hash"],
        "pipeline": [
            "compile_cinematic_shot",
            "generate_final_dialogue" if dialogue else "skip_dialogue",
            "generate_or_select_music",
            "build_scene_soundscape",
            "generate_lip_synced_video" if dialogue else "generate_video",
            "mix_and_edit_scene",
        ],
    }
