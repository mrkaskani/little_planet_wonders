"""Provide sound effects services for the LPW cinematic pipeline."""

from __future__ import annotations

from typing import Any

from lpw.audio.compiler import resolved_audio_context
from lpw.utils.hashing import stable_hash


SOUND_CATEGORIES = {
    "foley",
    "prop",
    "environment",
    "learning",
    "transition",
    "magical",
}
SAFE_VOLUMES = {"very-soft", "soft", "moderate"}


def compile_sound_cue_sheet(
    *,
    project_id: str,
    scene_id: str,
    shot_id: str,
    location_id: str,
    cues: list[dict[str, Any]],
    dialogue_present: bool,
    participation_pause: bool = False,
) -> dict[str, Any]:
    """Validate visible-action cues and compile a child-safe sound plan.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        location_id (str): Stable identifier of the location.
        cues (list[dict[str, Any]]): Structured audio or music cue definitions.
        dialogue_present (bool): Whether dialogue must have priority in the mix.
        participation_pause (bool): Whether the cue overlaps a child-response pause.
            Defaults to ``False``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """

    audio = resolved_audio_context(project_id)
    context = audio["sound_effects"]
    forbidden = {
        item.lower()
        for item in context.get("child_safety", {}).get("forbidden_qualities", [])
    }
    maximum_prominent = int(
        audio["mixing"]
        .get("sound_effects", {})
        .get("maximum_simultaneous_prominent_effects", 3)
    )
    compiled = []
    prominent = 0
    for index, cue in enumerate(cues, start=1):
        category = cue.get("category")
        if category not in SOUND_CATEGORIES:
            raise ValueError(f"Cue {index} has unsupported category {category!r}.")
        for field in ("cue_id", "source", "action", "story_purpose"):
            if not isinstance(cue.get(field), str) or not cue[field].strip():
                raise ValueError(f"Cue {index} requires non-empty {field}.")
        start = float(cue.get("start_seconds", 0))
        end = float(cue.get("end_seconds", start))
        if start < 0 or end < start:
            raise ValueError(f"Cue {index} has an invalid time range.")
        volume = cue.get("volume", "soft")
        if volume not in SAFE_VOLUMES:
            raise ValueError(f"Cue {index} has unsafe volume {volume!r}.")
        qualities = {str(item).lower() for item in cue.get("qualities", [])}
        prohibited = sorted(qualities & forbidden)
        if prohibited:
            raise ValueError(
                f"Cue {index} contains forbidden qualities: {', '.join(prohibited)}."
            )
        is_prominent = bool(cue.get("prominent", category in {"prop", "learning"}))
        prominent += int(is_prominent)
        compiled.append(
            {
                "event_id": f"sfx-{index:03d}",
                "cue_id": cue["cue_id"],
                "category": category,
                "source": cue["source"],
                "action": cue["action"],
                "story_purpose": cue["story_purpose"],
                "material": cue.get("material"),
                "asset": cue.get("asset"),
                "start_seconds": start,
                "end_seconds": end,
                "distance": cue.get("distance", "medium"),
                "position": cue.get("position", "center"),
                "volume": volume,
                "prominent": is_prominent,
                "continue_across_cut": bool(cue.get("continue_across_cut", False)),
                "relationship_to_dialogue": (
                    "reduce-beneath-dialogue" if dialogue_present else "normal"
                ),
                "provider": {
                    "status": (
                        "declared-unverified" if cue.get("asset") else "not-run"
                    ),
                    "reason": (
                        "Asset existence and format must be verified during execution."
                        if cue.get("asset")
                        else "An externally managed sound provider or library is required."
                    ),
                },
            }
        )
    if prominent > maximum_prominent:
        raise ValueError(
            f"Cue sheet has {prominent} prominent effects; maximum is {maximum_prominent}."
        )
    if participation_pause and any(item["prominent"] for item in compiled):
        raise ValueError("Participation pauses cannot contain prominent sound effects.")
    result = {
        "project_id": project_id,
        "scene_id": scene_id,
        "shot_id": shot_id,
        "location_id": location_id,
        "dialogue_present": dialogue_present,
        "participation_pause": participation_pause,
        "priority_order": audio["mixing"]["priority"],
        "cues": compiled,
        "constraints": [
            "align each cue with a visible or understandable source",
            "preserve clean dialogue and quiet participation space",
            "apply distance and location acoustics during mixing",
            "do not include effects in clean lip-sync dialogue",
        ],
    }
    result["cue_sheet_hash"] = stable_hash(result)
    return result
