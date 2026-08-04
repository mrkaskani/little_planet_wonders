from __future__ import annotations

from copy import deepcopy
from typing import Any

from little_planet_wonders.audio.defaults import AUDIO_DEFAULTS, VOICE_DEFAULTS
from little_planet_wonders.context.loader import load_audio_context, load_voice
from little_planet_wonders.models import DialogueRequest
from little_planet_wonders.utils.mappings import deep_merge


def resolved_audio_context(project_id: str) -> dict[str, Any]:
    context = deepcopy(AUDIO_DEFAULTS)
    loaded = load_audio_context(project_id)
    for key, value in loaded.items():
        context[key] = deep_merge(context.get(key, {}), value)
    return context


def resolved_voice_context(project_id: str, character_id: str) -> dict[str, Any]:
    voice = deep_merge(VOICE_DEFAULTS.get(character_id, {}), load_voice(project_id, character_id))
    if not voice.get("voice_identity"):
        raise ValueError(
            f"No voice profile is configured for character_id={character_id!r}."
        )
    return voice


def compile_dialogue_package(request: DialogueRequest) -> dict[str, Any]:
    if not request.text.strip():
        raise ValueError("Dialogue text cannot be empty.")
    if not 0 <= request.intensity <= 1:
        raise ValueError("Dialogue intensity must be between 0 and 1.")
    voice = resolved_voice_context(request.project_id, request.character_id)
    audio = resolved_audio_context(request.project_id)
    return {
        "project_id": request.project_id,
        "scene_id": request.scene_id,
        "shot_id": request.shot_id,
        "character_id": request.character_id,
        "text": request.text,
        "language": request.language,
        "voice_id": voice.get("generation", {}).get("voice_id"),
        "voice_profile": voice["voice_identity"],
        "performance": {
            **voice.get("performance", {}),
            "requested_emotion": request.emotion,
            "requested_intensity": request.intensity,
        },
        "pronunciation_dictionary": audio["pronunciation"],
        "technical": audio["audio_style"].get("dialogue", {}),
        "constraints": voice.get("consistency_constraints", []),
    }
