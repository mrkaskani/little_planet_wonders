from __future__ import annotations

import re
from pathlib import Path
from typing import Any


RESOLUTION = re.compile(r"^\d{2,5}x\d{2,5}$")
ASPECT_RATIO = re.compile(r"^\d+(?:\.\d+)?:\d+(?:\.\d+)?$")


def _continuity_warnings(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    checks = (
        ("camera", "screen_direction", "screen direction"),
        ("visual_state", "weather", "weather"),
        ("visual_state", "time_of_day", "time of day"),
        ("visual_state", "lighting_state", "lighting"),
        ("visual_state", "grade_reference", "color grade reference"),
    )
    for section, key, label in checks:
        before = previous.get(section, {}).get(key)
        after = current.get(section, {}).get(key)
        if before and after and before != after:
            warnings.append(f"Possible {label} discontinuity: {before!r} -> {after!r}.")

    previous_characters = previous.get("character_state", {})
    current_characters = current.get("character_state", {})
    for character_id in previous_characters.keys() & current_characters.keys():
        before = previous_characters[character_id]
        after = current_characters[character_id]
        for key, label in (
            ("position", "position"),
            ("looking_direction", "eye line"),
            ("wardrobe", "costume"),
            ("held_objects", "props"),
        ):
            if before.get(key) is not None and after.get(key) is not None and before[key] != after[key]:
                warnings.append(f"{character_id}: possible {label} discontinuity.")
    return warnings


def validate_edit_plan(edit_plan: dict[str, Any]) -> dict[str, list[str]]:
    """Validate visual, continuity, editing, and audio requirements."""

    blocking_errors: list[str] = []
    warnings: list[str] = []
    timeline = edit_plan.get("timeline")
    shots = edit_plan.get("shots")
    if not isinstance(timeline, dict):
        return {"blocking_errors": ["Timeline settings are missing."], "warnings": []}
    if not isinstance(shots, list) or not shots:
        blocking_errors.append("Timeline contains no shots.")
        shots = []

    frame_rate = timeline.get("frame_rate")
    if not isinstance(frame_rate, (int, float)) or frame_rate <= 0:
        blocking_errors.append("Timeline frame rate must be a positive number.")
    elif frame_rate != 24:
        warnings.append("Timeline frame rate differs from the 24 fps project standard.")
    resolution = timeline.get("resolution")
    if not isinstance(resolution, str) or not RESOLUTION.fullmatch(resolution):
        blocking_errors.append("Timeline resolution must use WIDTHxHEIGHT format.")
    aspect_ratio = timeline.get("aspect_ratio")
    if not isinstance(aspect_ratio, str) or not ASPECT_RATIO.fullmatch(aspect_ratio):
        blocking_errors.append("Timeline aspect ratio must use WIDTH:HEIGHT format.")

    previous_metadata: dict[str, Any] | None = None
    for shot in shots:
        shot_id = str(shot.get("shot_id", "unknown-shot"))
        in_frame = shot.get("in_frame")
        out_frame = shot.get("out_frame")
        if not isinstance(in_frame, int) or in_frame < 0:
            blocking_errors.append(f"{shot_id}: missing or invalid in frame.")
        if not isinstance(out_frame, int):
            blocking_errors.append(f"{shot_id}: missing or invalid out frame.")
        elif isinstance(in_frame, int) and out_frame <= in_frame:
            blocking_errors.append(f"{shot_id}: invalid frame range.")

        source = shot.get("source")
        if not source:
            warnings.append(f"{shot_id}: video source is not specified.")
        elif shot.get("require_existing_source", False) and not Path(source).is_file():
            blocking_errors.append(f"{shot_id}: video source does not exist: {source}")

        normalization = shot.get("normalization", {})
        for key in ("fps", "resolution", "aspect_ratio"):
            if normalization.get(key) in (None, ""):
                blocking_errors.append(f"{shot_id}: normalization {key} is missing.")

        color = shot.get("color", {})
        if not color.get("match_reference"):
            blocking_errors.append(f"{shot_id}: color reference is missing.")
        audio = shot.get("audio", {})
        if not audio.get("dialogue"):
            warnings.append(f"{shot_id}: dialogue mix rules are missing.")
        if not audio.get("ambience"):
            warnings.append(f"{shot_id}: ambience or room-tone rules are missing.")
        if not shot.get("transition_in"):
            blocking_errors.append(f"{shot_id}: transition type is missing.")

        metadata = shot.get("metadata", {})
        if previous_metadata:
            warnings.extend(
                f"{shot_id}: {warning}"
                for warning in _continuity_warnings(previous_metadata, metadata)
            )
        previous_metadata = metadata
        warnings.extend(f"{shot_id}: {message}" for message in shot.get("warnings", []))

    return {
        "blocking_errors": list(dict.fromkeys(blocking_errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }
