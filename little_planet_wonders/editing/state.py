from __future__ import annotations

from pathlib import Path
from typing import Any

from little_planet_wonders.config import runtime_root
from little_planet_wonders.utils.files import atomic_write_yaml
from little_planet_wonders.utils.identifiers import validate_identifier


def build_continuity_state(
    project_id: str, scene_id: str, edit_version: int, last_shot: dict[str, Any]
) -> dict[str, Any]:
    if edit_version < 1:
        raise ValueError("edit_version must be at least 1.")
    metadata = last_shot.get("metadata", last_shot)
    camera = metadata.get("camera", {})
    visual = metadata.get("visual_state", {})
    return {
        "project_id": project_id,
        "scene_id": scene_id,
        "edit_version": edit_version,
        "last_shot": {
            "id": metadata.get("shot_id"),
            "screen_direction": camera.get("screen_direction"),
            "camera_position": camera.get("camera_position"),
            "shot_size": camera.get("shot_size"),
        },
        "character_state": metadata.get("character_state", {}),
        "audio_state": metadata.get("audio_state", {}),
        "color_state": {
            "grade_reference": visual.get("grade_reference"),
            "lighting_state": visual.get("lighting_state"),
        },
    }


def save_continuity_state(
    project_id: str, scene_id: str, edit_version: int, last_shot: dict[str, Any]
) -> str:
    """Save generated edit state under /runtime, never under read-only /context."""

    project_id = validate_identifier(project_id, "project_id")
    scene_id = validate_identifier(scene_id, "scene_id")
    path: Path = runtime_root() / "continuity" / project_id / f"{scene_id}.yaml"
    atomic_write_yaml(path, build_continuity_state(project_id, scene_id, edit_version, last_shot))
    return str(path)
