"""Backward-compatible imports for cinematic audio planning."""

from little_planet_wonders.audio.compiler import (
    compile_dialogue_package,
    resolved_audio_context,
    resolved_voice_context,
)
from little_planet_wonders.audio.pipeline import compile_cinematic_shot
from little_planet_wonders.mcp.resources import (
    character_voice_context,
    project_audio_context,
)
from little_planet_wonders.mcp.tools import compile_dialogue
from little_planet_wonders.models import DialogueRequest

__all__ = [
    "DialogueRequest",
    "character_voice_context",
    "compile_cinematic_shot",
    "compile_dialogue",
    "compile_dialogue_package",
    "project_audio_context",
    "resolved_audio_context",
    "resolved_voice_context",
]
