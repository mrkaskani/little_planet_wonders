from __future__ import annotations

from pathlib import Path

import pytest

import lpw.editing.timeline as timeline_module
from lpw.config import PROJECT_ROOT
from lpw.editing.timeline import SceneFinalizationService
from lpw.generation.pipeline import GenerationPipelineError
from lpw.utils.files import load_yaml
from lpw.validation.finalization import (
    FinalShotValidationReport,
    record_render_approval,
    validate_approval,
)


APPROVAL_SCORES = {
    "character_identity": 5,
    "motion_quality": 4,
    "location_consistency": 5,
    "audio_consistency": 5,
    "lip_sync": 4,
}


def test_neon_city_recommendation_is_configured_as_classroom() -> None:
    project_directory = PROJECT_ROOT / "src" / "lpw" / "context" / "projects" / "riri-yoyo"
    project = load_yaml(project_directory / "project.yaml")
    export = load_yaml(project_directory / "export.yaml")
    timeline = load_yaml(
        project_directory / "scenes" / "garden-discovery" / "timeline.yaml"
    )

    assert project["project"]["id"] == "riri-yoyo"
    assert project["project"]["title"] == "Riri & Yoyo"
    assert timeline["scene"]["project_id"] == "riri-yoyo"
    assert all("renders/classroom/" in shot["video_path"] for shot in timeline["shots"])
    assert export["video"]["width"] == 1920
    assert export["video"]["height"] == 804


def test_creative_approval_scores_enforce_export_thresholds(tmp_path: Path) -> None:
    approval = tmp_path / "approval.json"
    approval.write_text(
        """{
          "status": "approved",
          "approved": true,
          "scores": {
            "character_identity": 5,
            "motion_quality": 2,
            "location_consistency": 5,
            "audio_consistency": 5,
            "lip_sync": 4
          }
        }""",
        encoding="utf-8",
    )
    thresholds = {
        "minimum_identity_score": 4,
        "minimum_motion_score": 3,
        "minimum_location_score": 4,
        "minimum_audio_score": 4,
        "minimum_lip_sync_score": 4,
    }

    issues = validate_approval(approval, thresholds)

    assert [issue.code for issue in issues] == ["APPROVAL_SCORE_TOO_LOW"]


def test_completed_wan_render_receives_one_immutable_scored_approval(
    tmp_path: Path,
) -> None:
    render_directory = (
        tmp_path / "renders" / "riri-yoyo" / "scene-001" / "shot-001" / "hash001"
    )
    render_directory.mkdir(parents=True)
    identity = {
        "project_id": "riri-yoyo",
        "scene_id": "scene-001",
        "shot_id": "shot-001",
        "package_hash": "hash001",
    }
    (render_directory / "generation-package.json").write_text(
        __import__("json").dumps(identity), encoding="utf-8"
    )
    (render_directory / "render-result.json").write_text(
        __import__("json").dumps({**identity, "status": "completed"}),
        encoding="utf-8",
    )

    approval = record_render_approval(
        render_directory=render_directory,
        reviewer="human-review",
        scores=APPROVAL_SCORES,
        continuity={"door_state": "closed"},
        project_root=tmp_path,
    )

    assert approval["status"] == "approved"
    assert approval["scores"]["character_identity"] == 5
    with pytest.raises(GenerationPipelineError, match="already has an approval"):
        record_render_approval(
            render_directory=render_directory,
            reviewer="human-review",
            scores=APPROVAL_SCORES,
            continuity={},
            project_root=tmp_path,
        )


def test_classroom_finalizer_rejects_missing_render_inputs_without_running_ffmpeg() -> None:
    result = SceneFinalizationService(PROJECT_ROOT).finalize_scene(
        "riri-yoyo", "garden-discovery", 1
    )

    assert result["status"] == "rejected"
    assert {issue["code"] for issue in result["blocking_errors"]} >= {
        "FILE_NOT_FOUND",
        "APPROVAL_MISSING",
        "AUDIO_STEM_MISSING",
    }


def test_successful_finalization_commits_runtime_continuity_only_after_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "workspace"
    context_root = tmp_path / "context"
    project_directory = context_root / "projects" / "riri-yoyo"
    scene_directory = project_directory / "scenes" / "scene-001"
    scene_directory.mkdir(parents=True)
    (project_directory / "project.yaml").write_text(
        "project:\n  id: riri-yoyo\n  title: Riri & Yoyo\n", encoding="utf-8"
    )
    (project_directory / "export.yaml").write_text(
        """video:
  width: 1920
  height: 804
  frame_rate: 24
  pixel_format: yuv420p
  working_codec: libx264
  working_quality_crf: 16
  delivery_codec: libx264
  delivery_quality_crf: 18
  delivery_preset: slow
audio:
  sample_rate: 48000
  channels: 2
  target_lufs: -16
  loudness_range: 7
  maximum_true_peak_db: -1.5
validation:
  allowed_frame_rate_difference: 0.01
  minimum_duration_seconds: 1
  maximum_black_segment_seconds: 0.5
  maximum_unplanned_freeze_seconds: 1
approval:
  minimum_identity_score: 4
  minimum_motion_score: 3
  minimum_location_score: 4
  minimum_audio_score: 4
  minimum_lip_sync_score: 4
""",
        encoding="utf-8",
    )
    video = project_root / "renders" / "riri-yoyo" / "scene-001" / "shot-001" / "hash001" / "output-00.mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    (video.parent / "approval.json").write_text(
        __import__("json").dumps(
            {
                "project_id": "riri-yoyo",
                "scene_id": "scene-001",
                "shot_id": "shot-001",
                "package_hash": "hash001",
                "status": "approved",
                "approved": True,
                "scores": APPROVAL_SCORES,
                "continuity": {"door_state": "closed"},
            }
        ),
        encoding="utf-8",
    )
    audio_paths = {
        "dialogue_stem": "audio/dialogue.wav",
        "music_stem": "audio/music.wav",
        "ambience_stem": "audio/ambience.wav",
        "sound_effects_stem": "audio/sfx.wav",
    }
    for relative in audio_paths.values():
        path = project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
    (scene_directory / "timeline.yaml").write_text(
        f"""scene:
  id: scene-001
  project_id: riri-yoyo
shots:
  - id: shot-001
    package_hash: hash001
    video_path: {video.relative_to(project_root).as_posix()}
    in_seconds: 0
    out_seconds: 2
    transition_after: hard-cut
audio:
  dialogue_stem: {audio_paths['dialogue_stem']}
  music_stem: {audio_paths['music_stem']}
  ambience_stem: {audio_paths['ambience_stem']}
  sound_effects_stem: {audio_paths['sound_effects_stem']}
output:
  filename_template: scene-001-v{{edit_version:03d}}.mp4
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CINEMATIC_CONTEXT_ROOT", str(context_root))
    monkeypatch.setenv("CINEMATIC_RUNTIME_ROOT", str(tmp_path / "runtime"))
    monkeypatch.setattr(
        timeline_module,
        "validate_shot",
        lambda **kwargs: FinalShotValidationReport(
            kwargs["shot_id"], True, {"format": {"duration": "2.0"}}, []
        ),
    )

    def copy_stage(**kwargs):
        destination = kwargs.get("destination") or kwargs.get("output_path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"rendered")
        return destination

    monkeypatch.setattr(timeline_module, "normalize_clip", copy_stage)
    monkeypatch.setattr(
        timeline_module,
        "concatenate_clips",
        lambda clip_paths, output_path: copy_stage(output_path=output_path),
    )
    monkeypatch.setattr(timeline_module, "mix_scene_audio", copy_stage)

    result = SceneFinalizationService(project_root).finalize_scene(
        "riri-yoyo", "scene-001", 2
    )

    assert result["status"] == "completed"
    assert result["edit_version"] == 2
    assert Path(result["output"]).is_file()
    assert result["continuity"]["state"] == {"door_state": "closed"}
    assert (
        tmp_path / "runtime" / "continuity" / "riri-yoyo" / "scene-001.yaml"
    ).is_file()
