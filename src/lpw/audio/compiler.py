"""Provide compiler services for the LPW cinematic pipeline."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from lpw.audio.defaults import AUDIO_DEFAULTS, VOICE_DEFAULTS
from lpw.context.loader import load_audio_context, load_voice
from lpw.models import DialogueRequest
from lpw.utils.mappings import deep_merge


def resolved_audio_context(project_id: str) -> dict[str, Any]:
    """Execute audio context.

    Args:
        project_id (str): Stable identifier of the project whose context is used.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    context = deepcopy(AUDIO_DEFAULTS)
    loaded = load_audio_context(project_id)
    for key, value in loaded.items():
        context[key] = deep_merge(context.get(key, {}), value)
    return context


def resolved_voice_context(project_id: str, character_id: str) -> dict[str, Any]:
    """Execute voice context.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        character_id (str): Stable identifier of the character.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    voice = deep_merge(VOICE_DEFAULTS.get(character_id, {}), load_voice(project_id, character_id))
    if not voice.get("voice_identity"):
        raise ValueError(
            f"No voice profile is configured for character_id={character_id!r}."
        )
    return voice


def compile_dialogue_package(request: DialogueRequest) -> dict[str, Any]:
    """Compile dialogue package.

    Args:
        request (DialogueRequest): Typed request containing the inputs for this
            operation.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    if not request.text.strip():
        raise ValueError("Dialogue text cannot be empty.")
    if not 0 <= request.intensity <= 1:
        raise ValueError("Dialogue intensity must be between 0 and 1.")
    voice = resolved_voice_context(request.project_id, request.character_id)
    audio = resolved_audio_context(request.project_id)
    references = voice.get("references", {})
    emotion_key = request.emotion.lower().replace(" ", "-").replace("_", "-")
    emotion_aliases = {
        "quiet-concern": "mild-concern",
        "concern": "mild-concern",
        "happy": "happy-gentle",
        "neutral": "neutral-friendly",
    }
    reference_key = emotion_aliases.get(emotion_key, emotion_key)
    return {
        "status": "instructions-only",
        "project_id": request.project_id,
        "scene_id": request.scene_id,
        "shot_id": request.shot_id,
        "character_id": request.character_id,
        "text": request.text,
        "language": request.language,
        "emotion": request.emotion,
        "intensity": request.intensity,
        "voice_id": voice.get("generation", {}).get("voice_id"),
        "voice_profile": voice["voice_identity"],
        "emotional_reference": references.get(reference_key)
        or references.get("neutral-friendly")
        or references.get("neutral"),
        "performance": {
            **voice.get("performance", {}),
            "requested_emotion": request.emotion,
            "requested_intensity": request.intensity,
        },
        "pronunciation_dictionary": audio["pronunciation"],
        "technical": audio["audio_style"].get("dialogue", {}),
        "constraints": voice.get("consistency_constraints", []),
        "exact_dialogue_required": True,
        "clean_audio_only": True,
        "authoritative_audio": False,
        "locking_rule": (
            "Only reviewed exact-dialogue audio may become authoritative for lip sync."
        ),
    }
