from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from little_planet_wonders.audio.compiler import compile_dialogue_package
from little_planet_wonders.audio.pipeline import compile_cinematic_shot as compile_pipeline
from little_planet_wonders.context.loader import load_project_context
from little_planet_wonders.editing.planner import (
    create_edit_plan as build_edit_plan,
    edit_cinematic_sequence as build_cinematic_sequence,
)
from little_planet_wonders.editing.state import save_continuity_state as persist_continuity_state
from little_planet_wonders.editing.validation import validate_edit_plan as run_edit_validation
from little_planet_wonders.generation.compiler import compile_wan_shot_package
from little_planet_wonders.generation.workflows import prepare_generation_job as build_generation_job
from little_planet_wonders.models import DialogueRequest, ShotRequest, ShotType


ALLOWED_SHOT_TYPES = {
    "draft",
    "text_to_video",
    "image_to_video",
    "dialogue",
    "performance",
}


def _shot_request(
    project_id: str,
    shot_id: str,
    scene_id: str,
    character_ids: list[str],
    location_id: str,
    shot_type: str,
    action: str,
    framing: str,
    lens: str,
    camera_height: str,
    camera_movement: str,
    emotional_tone: str = "",
    dialogue_audio: str | None = None,
    start_frame: str | None = None,
    performer_video: str | None = None,
    duration_seconds: int = 5,
    seed: int | None = None,
) -> ShotRequest:
    if shot_type not in ALLOWED_SHOT_TYPES:
        raise ValueError("shot_type must be one of: " + ", ".join(sorted(ALLOWED_SHOT_TYPES)))
    if not 1 <= duration_seconds <= 15:
        raise ValueError("duration_seconds must be between 1 and 15.")
    return ShotRequest(
        project_id=project_id,
        shot_id=shot_id,
        scene_id=scene_id,
        character_ids=character_ids,
        location_id=location_id,
        shot_type=cast(ShotType, shot_type),
        action=action,
        framing=framing,
        lens=lens,
        camera_height=camera_height,
        camera_movement=camera_movement,
        emotional_tone=emotional_tone,
        dialogue_audio=dialogue_audio,
        start_frame=start_frame,
        performer_video=performer_video,
        duration_seconds=duration_seconds,
        seed=seed,
    )


def inspect_project_context(
    project_id: str,
    character_ids: list[str] | None = None,
    location_id: str | None = None,
) -> dict[str, Any]:
    """Inspect the complete normalized context and its deterministic hash."""

    return load_project_context(
        project_id, character_ids=character_ids, location_id=location_id
    )


def compile_wan_shot(
    project_id: str,
    shot_id: str,
    scene_id: str,
    character_ids: list[str],
    location_id: str,
    shot_type: str,
    action: str,
    framing: str,
    lens: str,
    camera_height: str,
    camera_movement: str,
    emotional_tone: str = "",
    dialogue_audio: str | None = None,
    start_frame: str | None = None,
    performer_video: str | None = None,
    duration_seconds: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    request = _shot_request(**locals())
    return asdict(compile_wan_shot_package(request))


def compile_dialogue(
    project_id: str,
    scene_id: str,
    shot_id: str,
    character_id: str,
    text: str,
    emotion: str,
    intensity: float = 0.5,
    language: str = "Persian",
) -> dict[str, Any]:
    return compile_dialogue_package(DialogueRequest(**locals()))


def compile_cinematic_shot(
    project_id: str,
    shot_id: str,
    scene_id: str,
    character_ids: list[str],
    location_id: str,
    shot_type: str,
    action: str,
    framing: str,
    lens: str,
    camera_height: str,
    camera_movement: str,
    emotional_tone: str = "",
    dialogue_character_id: str | None = None,
    dialogue_text: str | None = None,
    dialogue_emotion: str = "neutral",
    dialogue_intensity: float = 0.5,
    dialogue_audio: str | None = None,
    start_frame: str | None = None,
    performer_video: str | None = None,
    duration_seconds: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    request_arguments = {
        key: value
        for key, value in locals().items()
        if key
        not in {
            "dialogue_character_id",
            "dialogue_text",
            "dialogue_emotion",
            "dialogue_intensity",
        }
    }
    shot_request = _shot_request(**request_arguments)
    dialogue_request = None
    if dialogue_text is not None:
        if not dialogue_character_id:
            raise ValueError("dialogue_character_id is required with dialogue_text.")
        dialogue_request = DialogueRequest(
            project_id=project_id,
            scene_id=scene_id,
            shot_id=shot_id,
            character_id=dialogue_character_id,
            text=dialogue_text,
            emotion=dialogue_emotion,
            intensity=dialogue_intensity,
        )
    return compile_pipeline(
        shot_request,
        dialogue_request=dialogue_request,
        dialogue_audio_path=dialogue_audio,
    )


def generate_cinematic_video(
    workflow_name: str,
    project_id: str,
    shot_id: str,
    scene_id: str,
    character_ids: list[str],
    location_id: str,
    shot_type: str,
    action: str,
    framing: str,
    lens: str,
    camera_height: str,
    camera_movement: str,
    emotional_tone: str = "",
    dialogue_audio: str | None = None,
    start_frame: str | None = None,
    performer_video: str | None = None,
    duration_seconds: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    arguments = locals().copy()
    arguments.pop("workflow_name")
    return build_generation_job(_shot_request(**arguments), workflow_name)


def create_edit_plan(
    project_id: str,
    shot_metadata_files: list[str],
    reference_shot_id: str,
    require_existing_sources: bool = False,
) -> dict[str, Any]:
    return build_edit_plan(
        project_id,
        shot_metadata_files,
        reference_shot_id,
        require_existing_sources=require_existing_sources,
    )


def validate_edit_plan(edit_plan: dict[str, Any]) -> dict[str, list[str]]:
    return run_edit_validation(edit_plan)


def edit_cinematic_sequence(
    project_id: str,
    scene_id: str,
    shot_metadata_files: list[str],
    reference_shot_id: str,
    output_path: str,
) -> dict[str, Any]:
    return build_cinematic_sequence(
        project_id, scene_id, shot_metadata_files, reference_shot_id, output_path
    )


def save_continuity_state(
    project_id: str,
    scene_id: str,
    edit_version: int,
    last_shot: dict[str, Any],
) -> dict[str, str]:
    return {
        "status": "saved",
        "path": persist_continuity_state(project_id, scene_id, edit_version, last_shot),
    }
