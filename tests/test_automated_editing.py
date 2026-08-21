from __future__ import annotations

import json
from pathlib import Path

import pytest

import lpw.editing.automation as automation_module
from lpw.editing.automation import AutomatedEditingPipeline
from lpw.validation.finalization import FinalShotValidationReport


SCORES = {
    "character_identity": 5,
    "facial_quality": 4,
    "motion_quality": 4,
    "camera_accuracy": 5,
    "location_consistency": 5,
    "continuity": 5,
    "lip_sync": 4,
    "editability": 5,
    "audio_consistency": 5,
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _automated_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = tmp_path / "workspace"
    context_root = tmp_path / "context"
    project = context_root / "projects" / "riri-yoyo"
    _write(context_root / "studio.yaml", "generation:\n  frame_rate: 24\n")
    _write(project / "project.yaml", "project:\n  id: riri-yoyo\n  title: Riri & Yoyo\n")
    _write(project / "continuity.yaml", "state:\n  door_state: closed\n")
    _write(
        project / "editing_style.yaml",
        "timeline:\n  frame_rate: 24\n  width: 1920\n  height: 804\n  resolution: 1920x804\n  aspect_ratio: '2.39:1'\n",
    )
    _write(
        project / "auto-editing.yaml",
        "automation:\n  mode: assisted\n  require_preview_approval: true\n"
        "preview:\n  width: 1280\n  height: 536\n  codec: libx264\n  crf: 24\n",
    )
    _write(project / "post-editing.yaml", "post_editing:\n  allow_story_reordering: false\n")
    _write(
        project / "take-selection.yaml",
        "take_selection_weights:\n  character_identity: 0.5\n  editability: 0.5\n",
    )
    _write(
        project / "export.yaml",
        """video:
  width: 1920
  height: 804
  frame_rate: 24
  pixel_format: yuv420p
audio: {sample_rate: 48000, channels: 2}
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
    )
    _write(
        project / "scenes" / "scene-001" / "edit-context.yaml",
        "scene:\n  id: scene-001\n  preferred_order: [shot-001]\n",
    )
    render = project_root / "renders" / "riri-yoyo" / "scene-001" / "shot-001" / "hash001"
    render.mkdir(parents=True)
    (render / "output-00.mp4").write_bytes(b"video")
    _write(
        render / "approval.json",
        json.dumps(
            {
                "project_id": "riri-yoyo",
                "scene_id": "scene-001",
                "shot_id": "shot-001",
                "package_hash": "hash001",
                "status": "approved",
                "approved": True,
                "scores": SCORES,
                "continuity": {"door_state": "closed"},
            }
        ),
    )
    _write(
        render / "generation-package.json",
        json.dumps({"context_hash": "context001", "package_hash": "hash001"}),
    )
    audio = {}
    for name in ("dialogue", "music", "ambience", "sfx"):
        relative = f"audio/{name}.wav"
        path = project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
        audio[name] = relative
    _write(
        project / "scenes" / "scene-001" / "timeline.yaml",
        f"""scene:
  id: scene-001
  project_id: riri-yoyo
shots:
  - id: shot-001
    package_hash: hash001
    video_path: {render.relative_to(project_root).as_posix()}/output-00.mp4
    in_seconds: 0
    out_seconds: 2
    transition_after: hard-cut
audio:
  dialogue_stem: {audio['dialogue']}
  music_stem: {audio['music']}
  ambience_stem: {audio['ambience']}
  sound_effects_stem: {audio['sfx']}
output:
  filename_template: scene-001-v{{edit_version:03d}}.mp4
""",
    )
    monkeypatch.setenv("CINEMATIC_CONTEXT_ROOT", str(context_root))
    return project_root


def test_three_stage_automated_editing_state_machine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _automated_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        automation_module,
        "validate_shot",
        lambda **kwargs: FinalShotValidationReport(
            kwargs["shot_id"], True, {"format": {"duration": "2.0"}}, []
        ),
    )

    def fake_normalize(**kwargs):
        destination = kwargs["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"preview-clip")
        return destination

    def fake_concat(clip_paths, output_path):
        output_path.write_bytes(b"preview")
        return output_path

    monkeypatch.setattr(automation_module, "normalize_clip", fake_normalize)
    monkeypatch.setattr(automation_module, "concatenate_clips", fake_concat)
    pipeline = AutomatedEditingPipeline(project_root)

    prepared = pipeline.prepare_automated_edit("riri-yoyo", "scene-001")
    automated = pipeline.automate_scene_edit("riri-yoyo", "scene-001", 1)
    approval = pipeline.approve_edit_preview(
        "riri-yoyo", "scene-001", 1, "director"
    )
    post = pipeline.post_edit_scene(
        "riri-yoyo",
        "scene-001",
        1,
        [
            {
                "id": "note-001",
                "timecode": "00:00:01:12",
                "type": "trim",
                "priority": "high",
                "instruction": "Hold the reaction longer.",
            }
        ],
    )

    assert prepared["status"] == "prepared"
    assert prepared["approved_takes"][0]["weighted_score"] == 5.0
    assert automated["status"] == "awaiting-approval"
    assert automated["edit_plan"]["video_events"][0]["event_id"] == "v001"
    assert Path(automated["preview"]).read_bytes() == b"preview"
    assert approval["status"] == "approved"
    assert post["status"] == "changes-requested"
    assert post["patch"]["operations"][0]["execution"] == "provider-required"


def test_approved_edit_creates_delivery_and_archive_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _automated_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        automation_module,
        "validate_shot",
        lambda **kwargs: FinalShotValidationReport(
            kwargs["shot_id"], True, {"format": {"duration": "2.0"}}, []
        ),
    )

    def fake_normalize(**kwargs):
        destination = kwargs["destination"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"preview-clip")
        return destination

    def fake_concat(clip_paths, output_path):
        output_path.write_bytes(b"preview")
        return output_path

    class FakeFinalizationService:
        def __init__(self, root: Path) -> None:
            self.root = root

        def finalize_scene(
            self, project_id: str, scene_id: str, edit_version: int
        ) -> dict[str, object]:
            output = self.root / "exports" / project_id / scene_id / "web.mp4"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"delivery")
            return {
                "status": "completed",
                "project_id": project_id,
                "scene_id": scene_id,
                "edit_version": edit_version,
                "output": str(output),
            }

    monkeypatch.setattr(automation_module, "normalize_clip", fake_normalize)
    monkeypatch.setattr(automation_module, "concatenate_clips", fake_concat)
    monkeypatch.setattr(
        automation_module, "SceneFinalizationService", FakeFinalizationService
    )
    pipeline = AutomatedEditingPipeline(project_root)
    pipeline.prepare_automated_edit("riri-yoyo", "scene-001")
    pipeline.automate_scene_edit("riri-yoyo", "scene-001", 1)
    pipeline.approve_edit_preview("riri-yoyo", "scene-001", 1, "director")

    result = pipeline.post_edit_scene("riri-yoyo", "scene-001", 1, [])

    archive = result["archive"]
    manifest_path = (
        project_root
        / "archive"
        / "riri-yoyo"
        / "scene-001"
        / "v001"
        / "archive-manifest.json"
    )
    assert result["status"] == "completed"
    assert Path(result["delivery_files"]["web"]).read_bytes() == b"delivery"
    assert manifest_path.is_file()
    assert archive["files"]["post_edit_patch"]["sha256"]
    assert result["provider_status"] == {
        "visual_cleanup": "not-run",
        "color_match": "not-run",
        "subtitles": "not-run",
        "master_profile": "not-run",
    }


def test_classroom_automated_editing_context_is_separated_by_concern() -> None:
    root = Path(__file__).resolve().parents[1] / "src" / "lpw" / "context" / "projects" / "riri-yoyo"

    assert (root / "editing_style.yaml").is_file()
    assert (root / "auto-editing.yaml").is_file()
    assert (root / "post-editing.yaml").is_file()
    assert (root / "take-selection.yaml").is_file()
    assert (root / "color-grade.yaml").is_file()
    assert (root / "subtitles.yaml").is_file()
    assert (root / "scenes" / "garden-discovery" / "edit-context.yaml").is_file()
