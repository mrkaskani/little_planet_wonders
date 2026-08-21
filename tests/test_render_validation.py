from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from lpw.config import PROJECT_ROOT
from lpw.context.compiler import ContextCompiler
from lpw.generation.pipeline import GenerationPipelineError
from lpw.validation.pipeline import RenderValidationPipeline
from lpw.validation.media import MediaValidator


class PassingMediaValidator:
    def run_checks(
        self,
        video_file: Path,
        project: dict[str, Any],
        shot: dict[str, Any],
        validation: dict[str, Any],
        rule_override: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "fixture-media",
                "status": "pass",
                "expected": "valid fixture",
                "actual": "valid fixture",
                "message": "Validation passed.",
            }
        ]


def _pipeline(tmp_path: Path) -> RenderValidationPipeline:
    return RenderValidationPipeline(
        PROJECT_ROOT,
        renders_root=tmp_path / "renders",
        media_validator=PassingMediaValidator(),
    )


def _source_video(tmp_path: Path, name: str = "source.mp4") -> Path:
    source = tmp_path / name
    source.write_bytes(b"immutable-video-fixture")
    return source


def _review_all(
    pipeline: RenderValidationPipeline,
    attempt_directory: str,
) -> None:
    report = pipeline.validate_attempt(attempt_directory)
    pipeline.record_semantic_review(
        attempt_directory,
        "reviewer-one",
        {
            check["id"]: {"status": "pass", "notes": "Checked."}
            for check in report["semantic_checks"]
        },
    )


def test_validation_context_compiles_scene_and_shot_rules() -> None:
    package = ContextCompiler().compile_validation_scene(
        "episode-001", "garden-discovery"
    )

    assert package["validation"]["automatic"]["video"]["expected_fps"] == 24
    assert package["validation"]["shots"]["shot-002"][
        "expected_duration_seconds"
    ] == 4
    assert "child-safety" in package["validation"]["semantic"]["required_checks"]


def test_attempts_are_versioned_and_snapshot_context(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    video = _source_video(tmp_path)

    first = pipeline.create_attempt(
        "episode-001", "garden-discovery", "shot-001", video
    )
    second = pipeline.create_attempt(
        "episode-001", "garden-discovery", "shot-001", video
    )

    assert first["generation_attempt"] == 1
    assert second["generation_attempt"] == 2
    first_directory = Path(first["attempt_directory"])
    assert (first_directory / "video.mp4").read_bytes() == video.read_bytes()
    assert (
        first_directory / "context-snapshot" / "compiled-context.json"
    ).is_file()
    assert (first_directory / "generation-package.json").is_file()


def test_approval_is_blocked_until_semantic_review_passes(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    attempt = pipeline.create_attempt(
        "episode-001",
        "garden-discovery",
        "shot-002",
        _source_video(tmp_path),
    )
    pipeline.validate_attempt(attempt["attempt_directory"])

    with pytest.raises(GenerationPipelineError, match="semantic checks pass"):
        pipeline.approve_attempt(attempt["attempt_directory"], "reviewer-one")

    _review_all(pipeline, attempt["attempt_directory"])
    approval = pipeline.approve_attempt(
        attempt["attempt_directory"], "reviewer-one", "Ready for assembly."
    )

    assert approval["approved"] is True
    assert len(approval["approval_hash"]) == 64
    with pytest.raises(GenerationPipelineError, match="already has"):
        pipeline.reject_attempt(
            attempt["attempt_directory"], "reviewer-two", "Changed decision."
        )


def test_release_requires_and_records_an_approved_attempt_for_every_shot(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    video = _source_video(tmp_path)

    with pytest.raises(GenerationPipelineError, match="no approved attempt"):
        pipeline.create_scene_release(
            "episode-001", "garden-discovery", video
        )

    for shot_id in ("shot-001", "shot-002", "shot-003", "shot-004"):
        attempt = pipeline.create_attempt(
            "episode-001", "garden-discovery", shot_id, video
        )
        _review_all(pipeline, attempt["attempt_directory"])
        pipeline.approve_attempt(attempt["attempt_directory"], "reviewer-one")

    release = pipeline.create_scene_release(
        "episode-001", "garden-discovery", video
    )

    assert release["approved"] is True
    assert release["release_number"] == 1
    assert [item["shot_id"] for item in release["approved_shot_attempts"]] == [
        "shot-001",
        "shot-002",
        "shot-003",
        "shot-004",
    ]
    release_directory = (
        tmp_path
        / "renders"
        / "garden-discovery"
        / "releases"
        / "release-0001"
    )
    assert (release_directory / "release-manifest.json").is_file()
    assert (release_directory / "validation-report.json").is_file()


def test_attempt_operations_reject_paths_outside_render_storage(
    tmp_path: Path,
) -> None:
    pipeline = _pipeline(tmp_path)
    outside = tmp_path / "attempt-9999"
    outside.mkdir()

    with pytest.raises(GenerationPipelineError, match="outside the renders root"):
        pipeline.validate_attempt(outside)


def test_attempt_validation_detects_modified_stored_media(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    attempt = pipeline.create_attempt(
        "episode-001",
        "garden-discovery",
        "shot-001",
        _source_video(tmp_path),
    )
    (Path(attempt["attempt_directory"]) / "video.mp4").write_bytes(b"modified")

    with pytest.raises(GenerationPipelineError, match="video hash mismatch"):
        pipeline.validate_attempt(attempt["attempt_directory"])


def test_media_validator_checks_probe_metadata_without_external_processes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    validator = MediaValidator()
    probe = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1280,
                "height": 720,
                "avg_frame_rate": "24/1",
                "pix_fmt": "yuv420p",
                "duration": "5.0",
                "nb_read_frames": "120",
            },
            {"codec_type": "audio"},
        ],
        "format": {"duration": "5.0"},
    }
    passed = {
        "id": "fixture",
        "status": "pass",
        "expected": True,
        "actual": True,
        "message": "Validation passed.",
    }
    monkeypatch.setattr(validator, "_probe_media", lambda _: probe)
    monkeypatch.setattr(validator, "_check_corruption", lambda _: passed)
    monkeypatch.setattr(validator, "_check_black_frames", lambda *_: passed)
    monkeypatch.setattr(validator, "_check_audio_peak", lambda *_: passed)
    rules = ContextCompiler().compile_validation_scene(
        "episode-001", "garden-discovery"
    )["validation"]

    checks = validator.run_checks(
        tmp_path / "unused.mp4",
        {"video": {"width": 1280, "height": 720, "fps": 24}},
        {"id": "shot-001", "duration_seconds": 5},
        rules,
    )

    assert all(check["status"] == "pass" for check in checks)
    assert {check["id"] for check in checks} >= {
        "video-stream",
        "audio-stream",
        "width",
        "height",
        "fps",
        "pixel-format",
        "duration",
        "frame-count",
    }
