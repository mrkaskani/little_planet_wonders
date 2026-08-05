"""Provide planner services for the LPW cinematic pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lpw.context.loader import load_project_context
from lpw.editing.validation import validate_edit_plan
from lpw.utils.files import load_json


def load_shot_metadata(metadata_path: str) -> dict[str, Any]:
    """Load shot metadata.

    Args:
        metadata_path (str): Metadata path used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    return load_json(Path(metadata_path).expanduser().resolve())


def create_edit_plan(
    project_id: str,
    shot_metadata_files: list[str],
    reference_shot_id: str,
    *,
    require_existing_sources: bool = False,
) -> dict[str, Any]:
    """Create edit plan.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        shot_metadata_files (list[str]): Shot metadata files used by this operation.
        reference_shot_id (str): Reference shot id used by this operation.
        require_existing_sources (bool): Require existing sources used by this
            operation. Defaults to ``False``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    context = load_project_context(project_id)
    editing = context["editing_style"]
    if not editing.get("timeline"):
        raise ValueError(f"Project {project_id!r} has no editing timeline configuration.")
    palette = context["color_palette"]
    audio = context["audio"]
    shots = [load_shot_metadata(path) for path in shot_metadata_files]
    plan_shots: list[dict[str, Any]] = []
    previous_shot: dict[str, Any] | None = None
    for shot in shots:
        edit = shot.get("edit", {})
        warnings: list[str] = []
        if previous_shot:
            previous_direction = previous_shot.get("camera", {}).get("screen_direction")
            current_direction = shot.get("camera", {}).get("screen_direction")
            if previous_direction and current_direction and previous_direction != current_direction:
                warnings.append("Possible screen-direction discontinuity.")
        plan_shots.append(
            {
                "shot_id": shot.get("shot_id"),
                "source": shot.get("video_path"),
                "require_existing_source": require_existing_sources,
                "in_frame": edit.get("preferred_in_frame"),
                "out_frame": edit.get("preferred_out_frame"),
                "normalization": {
                    "fps": editing["timeline"].get("frame_rate"),
                    "resolution": editing["timeline"].get("resolution"),
                    "aspect_ratio": editing["timeline"].get("aspect_ratio"),
                },
                "color": {
                    "match_reference": reference_shot_id,
                    "grade": palette.get("grade", palette.get("palette", {})),
                    "color_space": palette.get("color_management", {}),
                },
                "audio": {
                    "dialogue": audio.get("dialogue", {}),
                    "ambience": audio.get("ambience", {}),
                    "music": audio.get("music", {}),
                },
                "transition_in": edit.get("transition_in")
                or editing.get("cutting", {}).get("default_transition"),
                "metadata": shot,
                "warnings": warnings,
            }
        )
        previous_shot = shot
    return {
        "project_id": project_id,
        "reference_shot": reference_shot_id,
        "timeline": editing["timeline"],
        "shots": plan_shots,
        "continuity_rules": context["continuity"],
    }


def edit_cinematic_sequence(
    project_id: str,
    scene_id: str,
    shot_metadata_files: list[str],
    reference_shot_id: str,
    output_path: str,
) -> dict[str, Any]:
    """Execute cinematic sequence.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_metadata_files (list[str]): Shot metadata files used by this operation.
        reference_shot_id (str): Reference shot id used by this operation.
        output_path (str): Destination path for the generated output.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    plan = create_edit_plan(project_id, shot_metadata_files, reference_shot_id)
    validation = validate_edit_plan(plan)
    if validation["blocking_errors"]:
        return {
            "status": "rejected",
            "errors": validation["blocking_errors"],
            "warnings": validation["warnings"],
        }
    return {
        "status": "ready-for-render",
        "project_id": project_id,
        "scene_id": scene_id,
        "output_path": output_path,
        "edit_plan": plan,
        "warnings": validation["warnings"],
    }
