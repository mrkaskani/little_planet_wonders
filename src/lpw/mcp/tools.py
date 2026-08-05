"""Provide MCP tool handlers for LPW production workflows."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from lpw.audio.compiler import compile_dialogue_package
from lpw.audio.pipeline import compile_cinematic_shot as compile_pipeline
from lpw.audio.music import compile_music_cue_sheet as build_music_cue_sheet
from lpw.audio.sound_effects import (
    compile_sound_cue_sheet as build_sound_cue_sheet,
)
from lpw.audio.voice_production import VoiceProductionService
from lpw.config import PROJECT_ROOT
from lpw.context.loader import load_project_context
from lpw.context.pipeline import SceneContextPipeline
from lpw.editing.planner import (
    create_edit_plan as build_edit_plan,
    edit_cinematic_sequence as build_cinematic_sequence,
)
from lpw.editing.state import save_continuity_state as persist_continuity_state
from lpw.editing.timeline import SceneFinalizationService
from lpw.editing.automation import AutomatedEditingPipeline
from lpw.editing.validation import validate_edit_plan as run_edit_validation
from lpw.generation.compiler import compile_wan_shot_package
from lpw.generation.extension import CinematicExtensionPipeline
from lpw.generation.pipeline import SceneGenerationPipeline
from lpw.generation.render_service import render_wan_package
from lpw.generation.workflows import prepare_generation_job as build_generation_job
from lpw.models import DialogueRequest, ShotRequest, ShotType
from lpw.validation.pipeline import RenderValidationPipeline
from lpw.validation.finalization import record_render_approval


ALLOWED_SHOT_TYPES = {
    "draft",
    "text_to_video",
    "image_to_video",
    "dialogue",
}


def compile_scene_context(story_id: str, scene_id: str) -> dict[str, Any]:
    """Compile project, story, scene, and referenced shot YAML into one object.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return SceneContextPipeline().load_scene(story_id, scene_id)


def get_scene_summary(story_id: str, scene_id: str) -> dict[str, Any]:
    """Summarize duration, location, shot count, and generation modes.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return SceneContextPipeline().get_scene_summary(story_id, scene_id)


def build_scene_generation_plan(
    story_id: str, scene_id: str
) -> list[dict[str, Any]]:
    """Build an ordered generation plan from the scene's referenced shots.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.

    Returns:
        list[dict[str, Any]]: Result produced by the operation.
    """

    return SceneContextPipeline().build_generation_plan(story_id, scene_id)


def plan_scene_production(story_id: str, scene_id: str) -> dict[str, Any]:
    """Resolve tools and workflows for a scene without invoking external services.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return SceneGenerationPipeline(PROJECT_ROOT).produce_scene(
        story_id=story_id,
        scene_id=scene_id,
        dry_run=True,
    )


def create_render_attempt(
    story_id: str,
    scene_id: str,
    shot_id: str,
    video_file: str,
    dialogue_file: str | None = None,
) -> dict[str, Any]:
    """Store a new immutable render attempt and its compiled context snapshot.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        video_file (str): Path to the video file associated with the operation.
        dialogue_file (str | None): Dialogue file used by this operation. Defaults to
            ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).create_attempt(
        story_id, scene_id, shot_id, video_file, dialogue_file
    )


def validate_render_attempt(attempt_directory: str) -> dict[str, Any]:
    """Run FFprobe and FFmpeg validation for a stored attempt.

    Args:
        attempt_directory (str): Attempt directory used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).validate_attempt(attempt_directory)


def review_render_attempt(
    attempt_directory: str,
    reviewer: str,
    results: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Record human semantic-review results for a stored attempt.

    Args:
        attempt_directory (str): Attempt directory used by this operation.
        reviewer (str): Human reviewer identity recorded with the decision.
        results (dict[str, dict[str, str]]): Results used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).record_semantic_review(
        attempt_directory, reviewer, results
    )


def approve_render_attempt(
    attempt_directory: str,
    reviewer: str,
    notes: str = "",
    scores: dict[str, int] | None = None,
    continuity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Approve a validated attempt when all configured gates pass.

    Args:
        attempt_directory (str): Attempt directory used by this operation.
        reviewer (str): Human reviewer identity recorded with the decision.
        notes (str): Optional review or production notes. Defaults to ``''``.
        scores (dict[str, int] | None): Named review scores used by approval thresholds.
            Defaults to ``None``.
        continuity (dict[str, Any] | None): Continuity state approved for subsequent
            production. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).approve_attempt(
        attempt_directory, reviewer, notes, scores, continuity
    )


def reject_render_attempt(
    attempt_directory: str,
    reviewer: str,
    reason: str,
) -> dict[str, Any]:
    """Record an immutable rejection decision without deleting the attempt.

    Args:
        attempt_directory (str): Attempt directory used by this operation.
        reviewer (str): Human reviewer identity recorded with the decision.
        reason (str): Reason used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).reject_attempt(
        attempt_directory, reviewer, reason
    )


def create_scene_release(
    story_id: str,
    scene_id: str,
    final_video: str,
) -> dict[str, Any]:
    """Create a versioned release after every scene shot has an approval.

    Args:
        story_id (str): Stable identifier of the story to load or compile.
        scene_id (str): Stable identifier of the scene being processed.
        final_video (str): Final video used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return RenderValidationPipeline(PROJECT_ROOT).create_scene_release(
        story_id, scene_id, final_video
    )


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
    """Execute request.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        shot_id (str): Stable identifier of the shot being processed.
        scene_id (str): Stable identifier of the scene being processed.
        character_ids (list[str]): Character identifiers whose context should be
            included.
        location_id (str): Stable identifier of the location.
        shot_type (str): Shot type used by this operation.
        action (str): Action used by this operation.
        framing (str): Framing used by this operation.
        lens (str): Lens used by this operation.
        camera_height (str): Camera height used by this operation.
        camera_movement (str): Camera movement used by this operation.
        emotional_tone (str): Emotional tone used by this operation. Defaults to ``''``.
        dialogue_audio (str | None): Dialogue audio used by this operation. Defaults to
            ``None``.
        start_frame (str | None): Start frame used by this operation. Defaults to
            ``None``.
        performer_video (str | None): Performer video used by this operation. Defaults
            to ``None``.
        duration_seconds (int): Requested duration in seconds. Defaults to ``5``.
        seed (int | None): Optional deterministic generation seed. Defaults to ``None``.

    Returns:
        ShotRequest: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
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
    """Inspect the complete normalized context and its deterministic hash.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        character_ids (list[str] | None): Character identifiers whose context should be
            included. Defaults to ``None``.
        location_id (str | None): Stable identifier of the location. Defaults to
            ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

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
    """Compile wan shot.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        shot_id (str): Stable identifier of the shot being processed.
        scene_id (str): Stable identifier of the scene being processed.
        character_ids (list[str]): Character identifiers whose context should be
            included.
        location_id (str): Stable identifier of the location.
        shot_type (str): Shot type used by this operation.
        action (str): Action used by this operation.
        framing (str): Framing used by this operation.
        lens (str): Lens used by this operation.
        camera_height (str): Camera height used by this operation.
        camera_movement (str): Camera movement used by this operation.
        emotional_tone (str): Emotional tone used by this operation. Defaults to ``''``.
        dialogue_audio (str | None): Dialogue audio used by this operation. Defaults to
            ``None``.
        start_frame (str | None): Start frame used by this operation. Defaults to
            ``None``.
        performer_video (str | None): Performer video used by this operation. Defaults
            to ``None``.
        duration_seconds (int): Requested duration in seconds. Defaults to ``5``.
        seed (int | None): Optional deterministic generation seed. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
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
    """Compile dialogue.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        character_id (str): Stable identifier of the character.
        text (str): Exact text content used by the operation.
        emotion (str): Requested emotional delivery.
        intensity (float): Normalized requested performance intensity. Defaults to
            ``0.5``.
        language (str): Language used for dialogue and pronunciation rules. Defaults to
            ``'Persian'``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
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
    sound_effects: list[dict[str, Any]] | None = None,
    start_frame: str | None = None,
    performer_video: str | None = None,
    duration_seconds: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    """Compile cinematic shot.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        shot_id (str): Stable identifier of the shot being processed.
        scene_id (str): Stable identifier of the scene being processed.
        character_ids (list[str]): Character identifiers whose context should be
            included.
        location_id (str): Stable identifier of the location.
        shot_type (str): Shot type used by this operation.
        action (str): Action used by this operation.
        framing (str): Framing used by this operation.
        lens (str): Lens used by this operation.
        camera_height (str): Camera height used by this operation.
        camera_movement (str): Camera movement used by this operation.
        emotional_tone (str): Emotional tone used by this operation. Defaults to ``''``.
        dialogue_character_id (str | None): Dialogue character id used by this
            operation. Defaults to ``None``.
        dialogue_text (str | None): Dialogue text used by this operation. Defaults to
            ``None``.
        dialogue_emotion (str): Dialogue emotion used by this operation. Defaults to
            ``'neutral'``.
        dialogue_intensity (float): Dialogue intensity used by this operation. Defaults
            to ``0.5``.
        dialogue_audio (str | None): Dialogue audio used by this operation. Defaults to
            ``None``.
        sound_effects (list[dict[str, Any]] | None): Sound effects used by this
            operation. Defaults to ``None``.
        start_frame (str | None): Start frame used by this operation. Defaults to
            ``None``.
        performer_video (str | None): Performer video used by this operation. Defaults
            to ``None``.
        duration_seconds (int): Requested duration in seconds. Defaults to ``5``.
        seed (int | None): Optional deterministic generation seed. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    request_arguments = {
        key: value
        for key, value in locals().items()
        if key
        not in {
            "dialogue_character_id",
            "dialogue_text",
            "dialogue_emotion",
            "dialogue_intensity",
            "sound_effects",
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
        sound_effects=sound_effects,
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
    """Generate cinematic video.

    Args:
        workflow_name (str): Workflow name used by this operation.
        project_id (str): Stable identifier of the project whose context is used.
        shot_id (str): Stable identifier of the shot being processed.
        scene_id (str): Stable identifier of the scene being processed.
        character_ids (list[str]): Character identifiers whose context should be
            included.
        location_id (str): Stable identifier of the location.
        shot_type (str): Shot type used by this operation.
        action (str): Action used by this operation.
        framing (str): Framing used by this operation.
        lens (str): Lens used by this operation.
        camera_height (str): Camera height used by this operation.
        camera_movement (str): Camera movement used by this operation.
        emotional_tone (str): Emotional tone used by this operation. Defaults to ``''``.
        dialogue_audio (str | None): Dialogue audio used by this operation. Defaults to
            ``None``.
        start_frame (str | None): Start frame used by this operation. Defaults to
            ``None``.
        performer_video (str | None): Performer video used by this operation. Defaults
            to ``None``.
        duration_seconds (int): Requested duration in seconds. Defaults to ``5``.
        seed (int | None): Optional deterministic generation seed. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    arguments = locals().copy()
    arguments.pop("workflow_name")
    return build_generation_job(_shot_request(**arguments), workflow_name)


async def render_wan_i2v_shot(
    project_id: str,
    scene_id: str,
    shot_id: str,
    character_ids: list[str],
    location_id: str,
    action: str,
    start_frame: str,
    framing: str = "medium shot",
    lens: str = "50mm cinema lens",
    camera_height: str = "eye level",
    camera_movement: str = "locked camera",
    emotional_tone: str = "",
    duration_seconds: int = 5,
    seed: int | None = None,
) -> dict[str, Any]:
    """Compile and render one context-enforced Wan 2.2 I2V shot.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        character_ids (list[str]): Character identifiers whose context should be
            included.
        location_id (str): Stable identifier of the location.
        action (str): Action used by this operation.
        start_frame (str): Start frame used by this operation.
        framing (str): Framing used by this operation. Defaults to ``'medium shot'``.
        lens (str): Lens used by this operation. Defaults to ``'50mm cinema lens'``.
        camera_height (str): Camera height used by this operation. Defaults to ``'eye
            level'``.
        camera_movement (str): Camera movement used by this operation. Defaults to
            ``'locked camera'``.
        emotional_tone (str): Emotional tone used by this operation. Defaults to ``''``.
        duration_seconds (int): Requested duration in seconds. Defaults to ``5``.
        seed (int | None): Optional deterministic generation seed. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    request = _shot_request(
        project_id=project_id,
        shot_id=shot_id,
        scene_id=scene_id,
        character_ids=character_ids,
        location_id=location_id,
        shot_type="image_to_video",
        action=action,
        framing=framing,
        lens=lens,
        camera_height=camera_height,
        camera_movement=camera_movement,
        emotional_tone=emotional_tone,
        start_frame=start_frame,
        duration_seconds=duration_seconds,
        seed=seed,
    )
    return await render_wan_package(compile_wan_shot_package(request))


def create_edit_plan(
    project_id: str,
    shot_metadata_files: list[str],
    reference_shot_id: str,
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
    """
    return build_edit_plan(
        project_id,
        shot_metadata_files,
        reference_shot_id,
        require_existing_sources=require_existing_sources,
    )


def validate_edit_plan(edit_plan: dict[str, Any]) -> dict[str, list[str]]:
    """Validate edit plan.

    Args:
        edit_plan (dict[str, Any]): Edit plan used by this operation.

    Returns:
        dict[str, list[str]]: Result produced by the operation.
    """
    return run_edit_validation(edit_plan)


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
    return build_cinematic_sequence(
        project_id, scene_id, shot_metadata_files, reference_shot_id, output_path
    )


def save_continuity_state(
    project_id: str,
    scene_id: str,
    edit_version: int,
    last_shot: dict[str, Any],
) -> dict[str, str]:
    """Save continuity state.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit.
        last_shot (dict[str, Any]): Last shot used by this operation.

    Returns:
        dict[str, str]: Result produced by the operation.
    """
    return {
        "status": "saved",
        "path": persist_continuity_state(project_id, scene_id, edit_version, last_shot),
    }


def finalize_cinematic_scene(
    project_id: str,
    scene_id: str,
    edit_version: int = 1,
) -> dict[str, Any]:
    """Validate, assemble, mix, export, and commit an approved scene.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit. Defaults to ``1``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return SceneFinalizationService(PROJECT_ROOT).finalize_scene(
        project_id=project_id,
        scene_id=scene_id,
        edit_version=edit_version,
    )


def approve_wan_render(
    render_directory: str,
    reviewer: str,
    scores: dict[str, int],
    continuity: dict[str, Any],
    review_notes: list[str] | None = None,
) -> dict[str, Any]:
    """Record immutable scored approval metadata for a completed Wan render.

    Args:
        render_directory (str): Render directory used by this operation.
        reviewer (str): Human reviewer identity recorded with the decision.
        scores (dict[str, int]): Named review scores used by approval thresholds.
        continuity (dict[str, Any]): Continuity state approved for subsequent
            production.
        review_notes (list[str] | None): Structured or textual notes supplied by the
            reviewer. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return record_render_approval(
        render_directory=render_directory,
        reviewer=reviewer,
        scores=scores,
        continuity=continuity,
        review_notes=review_notes,
    )


def prepare_automated_edit(project_id: str, scene_id: str) -> dict[str, Any]:
    """Validate approved media and create an immutable prepared package.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return AutomatedEditingPipeline(PROJECT_ROOT).prepare_automated_edit(
        project_id, scene_id
    )


def automate_scene_edit(
    project_id: str,
    scene_id: str,
    prepared_package_version: int,
) -> dict[str, Any]:
    """Select takes, build an EDL, validate adjacency, and render a preview.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        prepared_package_version (int): Version of the prepared editing package.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return AutomatedEditingPipeline(PROJECT_ROOT).automate_scene_edit(
        project_id, scene_id, prepared_package_version
    )


def approve_edit_preview(
    project_id: str,
    scene_id: str,
    edit_version: int,
    reviewer: str,
    notes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Approve one immutable automated-edit preview version.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        edit_version (int): Positive version number of the edit.
        reviewer (str): Human reviewer identity recorded with the decision.
        notes (list[dict[str, Any]] | None): Optional review or production notes.
            Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return AutomatedEditingPipeline(PROJECT_ROOT).approve_edit_preview(
        project_id, scene_id, edit_version, reviewer, notes
    )


def post_edit_scene(
    project_id: str,
    scene_id: str,
    approved_edit_version: int,
    review_notes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compile review changes or finalize an unchanged approved edit.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        approved_edit_version (int): Version of the edit approved for post-production.
        review_notes (list[dict[str, Any]]): Structured or textual notes supplied by the
            reviewer.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return AutomatedEditingPipeline(PROJECT_ROOT).post_edit_scene(
        project_id, scene_id, approved_edit_version, review_notes
    )


def resolve_context_chain(
    project_id: str, scene_id: str, shot_id: str
) -> dict[str, Any]:
    """Resolve the pinned studio-to-shot context chain and return its hash.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return CinematicExtensionPipeline().resolve_context_chain(
        project_id, scene_id, shot_id
    )


def validate_context_chain(
    project_id: str, scene_id: str, shot_id: str
) -> dict[str, Any]:
    """Validate pinned versions, inheritance, and immutable context fields.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return CinematicExtensionPipeline().validate_context_chain(
        project_id, scene_id, shot_id
    )


def extend_cinematic_shot(
    project_id: str,
    scene_id: str,
    shot_id: str,
    target_duration_seconds: float,
    segment_duration_seconds: float = 4.0,
) -> dict[str, Any]:
    """Create a versioned short-segment extension plan without invoking models.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        target_duration_seconds (float): Total desired duration of the extended shot.
        segment_duration_seconds (float): Maximum duration of each generated segment.
            Defaults to ``4.0``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return CinematicExtensionPipeline().extend_cinematic_shot(
        project_id,
        scene_id,
        shot_id,
        target_duration_seconds,
        segment_duration_seconds,
    )


def compile_segment_context(
    project_id: str,
    scene_id: str,
    shot_id: str,
    extension_version: int,
    segment_id: str,
) -> dict[str, Any]:
    """Compile a segment after its predecessor has an approved end state.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        extension_version (int): Positive version number of the shot extension.
        segment_id (str): Stable identifier of the chained video segment.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return CinematicExtensionPipeline().compile_segment_context(
        project_id, scene_id, shot_id, extension_version, segment_id
    )


def approve_segment(
    project_id: str,
    scene_id: str,
    shot_id: str,
    extension_version: int,
    segment_id: str,
    generated_video_path: str,
    approved_end_frame_path: str,
    generated_frames: int,
    approved_end_frame: int,
    continuity_delta: dict[str, Any],
    analysis: dict[str, Any],
    reviewer: str,
) -> dict[str, Any]:
    """Approve real segment artifacts and commit their runtime continuity delta.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        extension_version (int): Positive version number of the shot extension.
        segment_id (str): Stable identifier of the chained video segment.
        generated_video_path (str): Path to the real video returned by a provider.
        approved_end_frame_path (str): Path to the reviewed stable segment end frame.
        generated_frames (int): Total number of frames produced by the provider.
        approved_end_frame (int): Index of the reviewed stable final frame.
        continuity_delta (dict[str, Any]): Small state delta produced by an approved
            segment.
        analysis (dict[str, Any]): Structured provider or validation analysis results.
        reviewer (str): Human reviewer identity recorded with the decision.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return CinematicExtensionPipeline().approve_segment(
        project_id=project_id,
        scene_id=scene_id,
        shot_id=shot_id,
        extension_version=extension_version,
        segment_id=segment_id,
        generated_video_path=generated_video_path,
        approved_end_frame_path=approved_end_frame_path,
        generated_frames=generated_frames,
        approved_end_frame=approved_end_frame,
        continuity_delta=continuity_delta,
        analysis=analysis,
        reviewer=reviewer,
    )


def prepare_exact_dialogue(
    project_id: str,
    episode_id: str,
    scene_id: str,
    shot_id: str,
    character_id: str,
    exact_dialogue: str,
    language: str,
    primary_emotion: str,
    ending_emotion: str | None = None,
    emotional_intensity: float = 0.4,
    speaking_speed: str = "slow-to-moderate",
    important_words: list[str] | None = None,
    pronunciation_notes: list[str] | None = None,
    pause_instructions: list[str] | None = None,
    audience_response_pause_seconds: float = 0,
    gesture_guidance: str | None = None,
    facial_expression_guidance: str | None = None,
) -> dict[str, Any]:
    """Prepare an exact clean-dialogue package; no voice provider is invoked.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        episode_id (str): Stable identifier of the episode being produced.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        character_id (str): Stable identifier of the character.
        exact_dialogue (str): Exact approved words that must be spoken once.
        language (str): Language used for dialogue and pronunciation rules.
        primary_emotion (str): Primary emotional direction for the performance.
        ending_emotion (str | None): Emotional direction at the end of the line.
            Defaults to ``None``.
        emotional_intensity (float): Child-safe normalized emotional intensity. Defaults
            to ``0.4``.
        speaking_speed (str): Speaking speed used by this operation. Defaults to
            ``'slow-to-moderate'``.
        important_words (list[str] | None): Important words used by this operation.
            Defaults to ``None``.
        pronunciation_notes (list[str] | None): Pronunciation notes used by this
            operation. Defaults to ``None``.
        pause_instructions (list[str] | None): Pause instructions used by this
            operation. Defaults to ``None``.
        audience_response_pause_seconds (float): Audience response pause seconds used by
            this operation. Defaults to ``0``.
        gesture_guidance (str | None): Gesture guidance used by this operation. Defaults
            to ``None``.
        facial_expression_guidance (str | None): Facial expression guidance used by this
            operation. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return VoiceProductionService().prepare_exact_dialogue(
        project_id=project_id,
        episode_id=episode_id,
        scene_id=scene_id,
        shot_id=shot_id,
        character_id=character_id,
        exact_dialogue=exact_dialogue,
        language=language,
        primary_emotion=primary_emotion,
        ending_emotion=ending_emotion,
        emotional_intensity=emotional_intensity,
        speaking_speed=speaking_speed,
        important_words=important_words,
        pronunciation_notes=pronunciation_notes,
        pause_instructions=pause_instructions,
        audience_response_pause_seconds=audience_response_pause_seconds,
        gesture_guidance=gesture_guidance,
        facial_expression_guidance=facial_expression_guidance,
    )


def lock_exact_dialogue(
    project_id: str,
    episode_id: str,
    scene_id: str,
    shot_id: str,
    character_id: str,
    dialogue_version: int,
    audio_path: str,
    verified_transcript: str,
    reviewer: str,
    review: dict[str, bool],
) -> dict[str, Any]:
    """Lock existing dialogue only after exact-text and safety review passes.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        episode_id (str): Stable identifier of the episode being produced.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        character_id (str): Stable identifier of the character.
        dialogue_version (int): Positive version number of the dialogue package.
        audio_path (str): Path to the audio asset being processed.
        verified_transcript (str): Reviewed transcript expected to match the dialogue
            exactly.
        reviewer (str): Human reviewer identity recorded with the decision.
        review (dict[str, bool]): Required review checks and their pass/fail values.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return VoiceProductionService().lock_exact_dialogue(
        project_id=project_id,
        episode_id=episode_id,
        scene_id=scene_id,
        shot_id=shot_id,
        character_id=character_id,
        dialogue_version=dialogue_version,
        audio_path=audio_path,
        verified_transcript=verified_transcript,
        reviewer=reviewer,
        review=review,
    )


def compile_dialogue_lip_sync_context(
    project_id: str,
    episode_id: str,
    scene_id: str,
    shot_id: str,
    character_id: str,
    dialogue_version: int,
) -> dict[str, Any]:
    """Compile video performance context from locked authoritative dialogue.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        episode_id (str): Stable identifier of the episode being produced.
        scene_id (str): Stable identifier of the scene being processed.
        shot_id (str): Stable identifier of the shot being processed.
        character_id (str): Stable identifier of the character.
        dialogue_version (int): Positive version number of the dialogue package.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    return VoiceProductionService().compile_lip_sync_context(
        project_id=project_id,
        episode_id=episode_id,
        scene_id=scene_id,
        shot_id=shot_id,
        character_id=character_id,
        dialogue_version=dialogue_version,
    )


def compile_sound_cue_sheet(
    project_id: str,
    scene_id: str,
    shot_id: str,
    location_id: str,
    cues: list[dict[str, Any]],
    dialogue_present: bool,
    participation_pause: bool = False,
) -> dict[str, Any]:
    """Compile visible-action, Foley, and learning cues separately from dialogue.

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
    """

    return build_sound_cue_sheet(
        project_id=project_id,
        scene_id=scene_id,
        shot_id=shot_id,
        location_id=location_id,
        cues=cues,
        dialogue_present=dialogue_present,
        participation_pause=participation_pause,
    )


def compile_music_cue_sheet(
    project_id: str,
    episode_id: str,
    scene_id: str,
    cues: list[dict[str, Any]],
    dialogue_present: bool,
    target_age: str = "two-to-five",
) -> dict[str, Any]:
    """Compile theme continuity, dialogue ducking, and participation pauses.

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
    """

    return build_music_cue_sheet(
        project_id=project_id,
        episode_id=episode_id,
        scene_id=scene_id,
        cues=cues,
        dialogue_present=dialogue_present,
        target_age=target_age,
    )
