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
    "performance",
}


def compile_scene_context(story_id: str, scene_id: str) -> dict[str, Any]:
    """Compile project, story, scene, and referenced shot YAML into one object."""

    return SceneContextPipeline().load_scene(story_id, scene_id)


def get_scene_summary(story_id: str, scene_id: str) -> dict[str, Any]:
    """Summarize duration, location, shot count, and generation modes."""

    return SceneContextPipeline().get_scene_summary(story_id, scene_id)


def build_scene_generation_plan(
    story_id: str, scene_id: str
) -> list[dict[str, Any]]:
    """Build an ordered generation plan from the scene's referenced shots."""

    return SceneContextPipeline().build_generation_plan(story_id, scene_id)


def plan_scene_production(story_id: str, scene_id: str) -> dict[str, Any]:
    """Resolve tools and workflows for a scene without invoking external services."""

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
    """Store a new immutable render attempt and its compiled context snapshot."""

    return RenderValidationPipeline(PROJECT_ROOT).create_attempt(
        story_id, scene_id, shot_id, video_file, dialogue_file
    )


def validate_render_attempt(attempt_directory: str) -> dict[str, Any]:
    """Run FFprobe and FFmpeg validation for a stored attempt."""

    return RenderValidationPipeline(PROJECT_ROOT).validate_attempt(attempt_directory)


def review_render_attempt(
    attempt_directory: str,
    reviewer: str,
    results: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Record human semantic-review results for a stored attempt."""

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
    """Approve a validated attempt when all configured gates pass."""

    return RenderValidationPipeline(PROJECT_ROOT).approve_attempt(
        attempt_directory, reviewer, notes, scores, continuity
    )


def reject_render_attempt(
    attempt_directory: str,
    reviewer: str,
    reason: str,
) -> dict[str, Any]:
    """Record an immutable rejection decision without deleting the attempt."""

    return RenderValidationPipeline(PROJECT_ROOT).reject_attempt(
        attempt_directory, reviewer, reason
    )


def create_scene_release(
    story_id: str,
    scene_id: str,
    final_video: str,
) -> dict[str, Any]:
    """Create a versioned release after every scene shot has an approval."""

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
    sound_effects: list[dict[str, Any]] | None = None,
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
    """Compile and render one context-enforced Wan 2.2 I2V shot."""

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


def finalize_cinematic_scene(
    project_id: str,
    scene_id: str,
    edit_version: int = 1,
) -> dict[str, Any]:
    """Validate, assemble, mix, export, and commit an approved scene."""

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
    """Record immutable scored approval metadata for a completed Wan render."""

    return record_render_approval(
        render_directory=render_directory,
        reviewer=reviewer,
        scores=scores,
        continuity=continuity,
        review_notes=review_notes,
    )


def prepare_automated_edit(project_id: str, scene_id: str) -> dict[str, Any]:
    """Validate approved media and create an immutable prepared package."""

    return AutomatedEditingPipeline(PROJECT_ROOT).prepare_automated_edit(
        project_id, scene_id
    )


def automate_scene_edit(
    project_id: str,
    scene_id: str,
    prepared_package_version: int,
) -> dict[str, Any]:
    """Select takes, build an EDL, validate adjacency, and render a preview."""

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
    """Approve one immutable automated-edit preview version."""

    return AutomatedEditingPipeline(PROJECT_ROOT).approve_edit_preview(
        project_id, scene_id, edit_version, reviewer, notes
    )


def post_edit_scene(
    project_id: str,
    scene_id: str,
    approved_edit_version: int,
    review_notes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compile review changes or finalize an unchanged approved edit."""

    return AutomatedEditingPipeline(PROJECT_ROOT).post_edit_scene(
        project_id, scene_id, approved_edit_version, review_notes
    )


def resolve_context_chain(
    project_id: str, scene_id: str, shot_id: str
) -> dict[str, Any]:
    """Resolve the pinned studio-to-shot context chain and return its hash."""

    return CinematicExtensionPipeline().resolve_context_chain(
        project_id, scene_id, shot_id
    )


def validate_context_chain(
    project_id: str, scene_id: str, shot_id: str
) -> dict[str, Any]:
    """Validate pinned versions, inheritance, and immutable context fields."""

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
    """Create a versioned short-segment extension plan without invoking models."""

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
    """Compile a segment after its predecessor has an approved end state."""

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
    """Approve real segment artifacts and commit their runtime continuity delta."""

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
    """Prepare an exact clean-dialogue package; no voice provider is invoked."""

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
    """Lock existing dialogue only after exact-text and safety review passes."""

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
    """Compile video performance context from locked authoritative dialogue."""

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
    """Compile visible-action, Foley, and learning cues separately from dialogue."""

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
    """Compile theme continuity, dialogue ducking, and participation pauses."""

    return build_music_cue_sheet(
        project_id=project_id,
        episode_id=episode_id,
        scene_id=scene_id,
        cues=cues,
        dialogue_present=dialogue_present,
        target_age=target_age,
    )
