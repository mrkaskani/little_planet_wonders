from __future__ import annotations

from pathlib import Path

import pytest

from lpw.context.chaining import ContextChainError, ContextChainResolver
from lpw.generation.extension import CinematicExtensionPipeline
from lpw.generation.pipeline import GenerationPipelineError


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_classroom_shot_resolves_a_pinned_context_chain() -> None:
    result = CinematicExtensionPipeline().resolve_context_chain(
        "classroom", "rooftop-confrontation", "shot-004"
    )

    assert result["context"]["project"]["id"] == "classroom"
    assert result["context"]["camera"]["lens"] == "85mm"
    assert result["context"]["technical"]["frame_rate"] == 24
    assert result["base_context_hash"]
    assert all(item["version"] == 1 for item in result["context_chain"])


def test_resolver_rejects_cycles_latest_and_immutable_changes(tmp_path: Path) -> None:
    source = tmp_path / "context"
    state = tmp_path / "runtime"
    _write(
        source / "projects" / "a" / "project.yaml",
        "id: a\ntype: project-context\nversion: 1\n"
        "extends: [cinema://projects/b@1]\n",
    )
    _write(
        source / "projects" / "b" / "project.yaml",
        "id: b\ntype: project-context\nversion: 1\n"
        "extends: [cinema://projects/a@1]\n",
    )
    resolver = ContextChainResolver(source, state)

    with pytest.raises(ContextChainError, match="Circular"):
        resolver.resolve("cinema://projects/a@1")
    with pytest.raises(ContextChainError, match="exact version"):
        resolver.resolve("cinema://projects/a@latest")

    _write(
        source / "studio" / "cinematic-defaults.yaml",
        "id: defaults\ntype: studio-context\nversion: 1\n"
        "technical: {frame_rate: 24}\n"
        "merge_policy:\n  immutable: [technical.frame_rate]\n",
    )
    _write(
        source / "projects" / "c" / "project.yaml",
        "id: c\ntype: project-context\nversion: 1\n"
        "extends: [cinema://studio/cinematic-defaults@1]\n"
        "technical: {frame_rate: 30}\n",
    )
    with pytest.raises(ContextChainError, match="immutable"):
        resolver.resolve("cinema://projects/c@1")


def test_extension_requires_approved_real_artifacts_before_next_segment(
    tmp_path: Path,
) -> None:
    source = Path(__file__).resolve().parents[1] / "src" / "lpw" / "context"
    state = tmp_path / "runtime"
    pipeline = CinematicExtensionPipeline(source, state)

    plan = pipeline.extend_cinematic_shot(
        "classroom", "rooftop-confrontation", "shot-004", 12
    )

    assert plan["status"] == "awaiting-segment-generation"
    assert len(plan["segments"]) == 3
    assert plan["segments"][0]["status"] == "ready-for-generation"
    assert plan["segments"][1]["status"] == "blocked"
    first_directory = (
        state
        / "extensions"
        / "classroom"
        / "rooftop-confrontation"
        / "shot-004"
        / "v001"
        / "segments"
        / "shot-004-segment-001"
    )
    assert (first_directory / "compiled-context.json").is_file()
    assert (first_directory / "context-chain.json").is_file()
    assert (first_directory / "runtime-input-state.yaml").is_file()

    with pytest.raises(GenerationPipelineError, match="approved predecessor"):
        pipeline.compile_segment_context(
            "classroom",
            "rooftop-confrontation",
            "shot-004",
            1,
            "shot-004-segment-002",
        )

    video = tmp_path / "generated.mp4"
    frame = tmp_path / "stable-frame.png"
    video.write_bytes(b"real-provider-output")
    frame.write_bytes(b"approved-stable-frame")
    approval = pipeline.approve_segment(
        project_id="classroom",
        scene_id="rooftop-confrontation",
        shot_id="shot-004",
        extension_version=1,
        segment_id="shot-004-segment-001",
        generated_video_path=str(video),
        approved_end_frame_path=str(frame),
        generated_frames=117,
        approved_end_frame=108,
        continuity_delta={
            "character_changes": {
                "roxana": {"head_direction": {"from": "down", "to": "raised"}}
            },
            "audio_state": {"music_position_seconds": 4.0},
        },
        analysis={"blocking_errors": [], "rejection_reason": "unstable tail"},
        reviewer="director",
    )
    second = pipeline.compile_segment_context(
        "classroom",
        "rooftop-confrontation",
        "shot-004",
        1,
        "shot-004-segment-002",
    )

    assert approval["status"] == "approved"
    assert approval["runtime_state_hash"]
    assert approval["edit_event"]["event_id"] == "v-shot-004-001"
    assert second["runtime_state_hash"]
    assert second["context"]["runtime_state"]["character_changes"]["roxana"]
    assert (first_directory / "continuity-delta.yaml").is_file()
    assert (first_directory / "runtime-output-state.yaml").is_file()
    second_directory = first_directory.parent / "shot-004-segment-002"
    assert (second_directory / "start-frame.png").read_bytes() == (
        b"approved-stable-frame"
    )
