"""Provide state services for the LPW cinematic pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lpw.config import runtime_root
from lpw.utils.files import atomic_write_yaml, load_yaml
from lpw.utils.identifiers import validate_identifier


def build_continuity_state(
    project_id: str, scene_id: str, edit_version: int, last_shot: dict[str, Any]
) -> dict[str, Any]:
    """Build continuity state.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit.
        last_shot (dict[str, Any]): Last shot used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
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
    """Save generated edit state under /runtime, never under read-only /context.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit.
        last_shot (dict[str, Any]): Last shot used by this operation.

    Returns:
        str: Result produced by the operation.
    """

    project_id = validate_identifier(project_id, "project_id")
    scene_id = validate_identifier(scene_id, "scene_id")
    path: Path = runtime_root() / "continuity" / project_id / f"{scene_id}.yaml"
    atomic_write_yaml(path, build_continuity_state(project_id, scene_id, edit_version, last_shot))
    return str(path)


def commit_scene_continuity(
    *,
    project_id: str,
    scene_id: str,
    edit_version: int,
    last_shot_approval: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Commit authoritative continuity only after a successful final export.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit.
        last_shot_approval (dict[str, Any]): Last shot approval used by this operation.
        output_path (Path): Destination path for the generated output.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """

    from datetime import datetime, timezone

    project_id = validate_identifier(project_id, "project_id")
    scene_id = validate_identifier(scene_id, "scene_id")
    if edit_version < 1:
        raise ValueError("edit_version must be at least 1.")
    path = runtime_root() / "continuity" / project_id / f"{scene_id}.yaml"
    current = load_yaml(path, required=False)
    continuity = {
        **current,
        "last_completed_scene": scene_id,
        "last_edit_version": edit_version,
        "last_output": str(output_path.resolve()),
        "last_updated_utc": datetime.now(timezone.utc).isoformat(),
        "state": last_shot_approval.get("continuity", {}),
    }
    atomic_write_yaml(path, continuity)
    return continuity
