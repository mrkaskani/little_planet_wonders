"""Provide prompts services for the LPW cinematic pipeline."""

from __future__ import annotations

import json
from typing import Any

from lpw.models import ShotRequest


DEFAULT_NEGATIVE_PROMPT = [
    "character identity change",
    "different face",
    "different apparent age",
    "different hairstyle",
    "unapproved wardrobe change",
    "location geometry change",
    "moving permanent landmarks",
    "incorrect screen direction",
    "incorrect eye line",
    "random camera orbit",
    "rapid camera zoom",
    "excessive camera shake",
    "rubber-like motion",
    "unnatural body movement",
    "malformed anatomy",
    "duplicated body parts",
    "unstable background",
    "lighting flicker",
    "oversaturated colors",
    "plastic skin",
    "text",
    "subtitles",
    "logo",
    "watermark",
]


def yaml_like_section(title: str, value: Any) -> str:
    """Execute like section.

    Args:
        title (str): Title used by this operation.
        value (Any): Value inspected or transformed by the helper.

    Returns:
        str: Result produced by the operation.
    """
    if value in (None, {}, []):
        return ""
    formatted = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return f"[{title}]\n{formatted}"


def build_positive_prompt(request: ShotRequest, context: dict[str, Any]) -> str:
    """Build positive prompt.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.
        context (dict[str, Any]): Resolved cinematic context used by the operation.

    Returns:
        str: Result produced by the operation.
    """
    sections = [
        yaml_like_section("PROJECT VISUAL DIRECTION", context.get("project")),
        yaml_like_section("VISUAL STYLE", context.get("visual_style")),
        yaml_like_section("CHARACTERS", context.get("characters")),
        yaml_like_section("LOCATION", context.get("location")),
        yaml_like_section("COLOR PALETTE", context.get("color_palette")),
        yaml_like_section("LIGHTING", context.get("lighting")),
        yaml_like_section("CAMERA LANGUAGE", context.get("camera_language")),
        yaml_like_section("CURRENT CONTINUITY STATE", context.get("continuity")),
    ]
    shot_section = f"""
[SHOT INSTRUCTIONS]
Shot ID: {request.shot_id}
Scene ID: {request.scene_id}
Framing: {request.framing}
Lens: {request.lens}
Camera height: {request.camera_height}
Camera movement: {request.camera_movement}
Emotional tone: {request.emotional_tone or "inherit from scene"}
Duration: approximately {request.duration_seconds} seconds

Primary action:
{request.action}
""".strip()
    continuity_section = """
[MANDATORY CONSISTENCY]
Preserve the approved character identity and facial proportions.
Preserve hairstyle, wardrobe, accessories and physical condition.
Preserve the established location geometry and permanent landmarks.
Preserve the approved color palette and lighting direction.
Preserve screen direction and character eye lines.
Use one dominant camera movement.
Use one clearly readable primary character action.
Keep motion physically plausible and cinematic.
Do not redesign any established visual element.
""".strip()
    return "\n\n".join(
        section for section in [*sections, shot_section, continuity_section] if section
    )


def extract_negative_values(value: Any) -> list[str]:
    """Extract negative values.

    Args:
        value (Any): Value inspected or transformed by the helper.

    Returns:
        list[str]: Result produced by the operation.
    """
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in extract_negative_values(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in extract_negative_values(child)]
    return []


def build_negative_prompt(context: dict[str, Any]) -> str:
    """Build negative prompt.

    Args:
        context (dict[str, Any]): Resolved cinematic context used by the operation.

    Returns:
        str: Result produced by the operation.
    """
    project_negative = extract_negative_values(context.get("negative_prompt", {}))
    forbidden_styles = extract_negative_values(
        context.get("visual_style", {}).get("forbidden", [])
    )
    return ", ".join(
        dict.fromkeys([*DEFAULT_NEGATIVE_PROMPT, *project_negative, *forbidden_styles])
    )
