from __future__ import annotations

import json

import yaml

from little_planet_wonders.audio.compiler import (
    resolved_audio_context,
    resolved_voice_context,
)
from little_planet_wonders.config import context_root
from little_planet_wonders.context.loader import (
    get_project_directory,
    load_character,
    load_location,
    load_project_context,
)
from little_planet_wonders.utils.files import load_yaml


def studio_context() -> str:
    return yaml.safe_dump(
        load_yaml(context_root() / "studio.yaml"),
        sort_keys=False,
        allow_unicode=True,
    )


def project_context(project_id: str) -> str:
    return yaml.safe_dump(
        load_project_context(project_id), sort_keys=False, allow_unicode=True
    )


def character_context(project_id: str, character_id: str) -> str:
    return yaml.safe_dump(
        load_character(get_project_directory(project_id), character_id),
        sort_keys=False,
        allow_unicode=True,
    )


def location_context(project_id: str, location_id: str) -> str:
    return yaml.safe_dump(
        load_location(get_project_directory(project_id), location_id),
        sort_keys=False,
        allow_unicode=True,
    )


def project_audio_context(project_id: str) -> str:
    return json.dumps(resolved_audio_context(project_id), ensure_ascii=False, indent=2)


def character_voice_context(project_id: str, character_id: str) -> str:
    return json.dumps(
        resolved_voice_context(project_id, character_id), ensure_ascii=False, indent=2
    )


def editing_context(project_id: str) -> str:
    context = load_project_context(project_id)
    result = {
        "editing": context["editing_style"],
        "palette": context["color_palette"],
        "audio": context["audio"],
        "camera": context["camera_language"],
        "continuity": context["continuity"],
    }
    return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
