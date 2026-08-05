"""Provide music services for the LPW cinematic pipeline."""

from __future__ import annotations

from typing import Any

from lpw.audio.compiler import resolved_audio_context
from lpw.utils.hashing import stable_hash


MUSIC_ACTIONS = {"start", "continue", "reduce", "resolve", "transition", "stop"}
ENERGY_LEVELS = {"very-low": 0, "low": 1, "low-to-moderate": 2, "moderate": 3}


def compile_music_cue_sheet(
    *,
    project_id: str,
    episode_id: str,
    scene_id: str,
    cues: list[dict[str, Any]],
    dialogue_present: bool,
    target_age: str = "two-to-five",
) -> dict[str, Any]:
    """Compile reusable music cues while preserving dialogue and response pauses.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        episode_id (str): Stable identifier of the episode being produced.
        scene_id (str): Stable identifier of the scene being processed.
        cues (list[dict[str, Any]]): Structured audio or music cue definitions.
        dialogue_present (bool): Whether dialogue must have priority in the mix.
        target_age (str): Audience age range used by safety rules. Defaults to ``'two-
            to-five'``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """

    music = resolved_audio_context(project_id)["music"]
    safety = music.get("child_safety", {})
    maximum_energy = safety.get("maximum_energy", "moderate")
    maximum_value = ENERGY_LEVELS.get(maximum_energy, 3)
    forbidden_instruments = {
        item.lower() for item in music.get("identity", {}).get("forbidden", [])
    }
    compiled = []
    for index, cue in enumerate(cues, start=1):
        action = cue.get("action")
        if action not in MUSIC_ACTIONS:
            raise ValueError(f"Music cue {index} has unsupported action {action!r}.")
        cue_id = cue.get("cue_id")
        if not isinstance(cue_id, str) or not cue_id.strip():
            raise ValueError(f"Music cue {index} requires cue_id.")
        start = float(cue.get("start_seconds", 0))
        end = float(cue.get("end_seconds", start))
        if start < 0 or end < start:
            raise ValueError(f"Music cue {index} has an invalid time range.")
        energy = cue.get("energy", "low")
        if energy not in ENERGY_LEVELS or ENERGY_LEVELS[energy] > maximum_value:
            raise ValueError(f"Music cue {index} exceeds the maximum energy.")
        instruments = [str(item) for item in cue.get("instrumentation", [])]
        prohibited = sorted(
            instrument
            for instrument in instruments
            if instrument.lower() in forbidden_instruments
        )
        if prohibited:
            raise ValueError(
                f"Music cue {index} uses forbidden instruments/styles: "
                f"{', '.join(prohibited)}."
            )
        participation = cue.get("participation_pause")
        if participation:
            duration = float(participation.get("duration_seconds", 0))
            if not 3 <= duration <= 5:
                raise ValueError("Music participation pauses must be 3 to 5 seconds.")
        compiled.append(
            {
                "event_id": f"music-{index:03d}",
                "cue_id": cue_id,
                "action": action,
                "theme": cue.get("theme"),
                "start_seconds": start,
                "end_seconds": end,
                "timeline_position_seconds": cue.get("timeline_position_seconds", 0),
                "emotion": cue.get("emotion", "calm"),
                "learning_purpose": cue.get("learning_purpose"),
                "tempo_bpm": cue.get("tempo_bpm"),
                "energy": energy,
                "instrumentation": instruments,
                "asset": cue.get("asset"),
                "dialogue_relationship": (
                    "duck-and-simplify" if dialogue_present else "normal"
                ),
                "participation_pause": (
                    {
                        **participation,
                        "remove_percussion": True,
                        "no_new_melody": True,
                        "do_not_reveal_answer": True,
                    }
                    if participation
                    else None
                ),
                "continue_into_next_scene": bool(
                    cue.get("continue_into_next_scene", False)
                ),
                "provider": {
                    "status": (
                        "declared-unverified" if cue.get("asset") else "not-run"
                    ),
                    "reason": (
                        "Asset existence and format must be verified during execution."
                        if cue.get("asset")
                        else "An externally managed music provider or library is required."
                    ),
                },
            }
        )
    result = {
        "project_id": project_id,
        "episode_id": episode_id,
        "scene_id": scene_id,
        "target_age": target_age,
        "dialogue_present": dialogue_present,
        "series_identity": music.get("identity", {}),
        "cues": compiled,
        "mixing": {
            **music.get("mixing", {}),
            "dialogue_has_priority": True,
            "preserve_ambience_identity": True,
        },
        "constraints": [
            "use recognizable approved themes rather than unrelated new motifs",
            "reduce music beneath dialogue and important visible-action sounds",
            "preserve silence and child-response time",
            "do not include dialogue, ambience, or sound effects in music assets",
        ],
    }
    result["cue_sheet_hash"] = stable_hash(result)
    return result
