from __future__ import annotations

from pathlib import Path

import pytest

from lpw.config import PROJECT_ROOT
from lpw.context.compiler import ContextCompiler, ContextCompilerError
from lpw.generation.pipeline import GenerationPipelineError, SceneGenerationPipeline
from lpw.mcp.tools import plan_scene_production


STORY_ID = "episode-001"
SCENE_ID = "rooftop-confrontation"


def test_compiler_resolves_production_tools_and_used_workflows() -> None:
    package = ContextCompiler().compile_production_scene(STORY_ID, SCENE_ID)

    assert sorted(package["tools"]) == [
        "ambience-generator",
        "ffmpeg",
        "keyframe-qwen",
        "latent-sync",
        "music-generator",
        "sound-effect-generator",
        "voice-cosyvoice",
        "wan22-comfyui",
    ]
    assert sorted(package["workflows"]) == ["wan-i2v", "wan-s2v", "wan-t2v"]
    assert package["workflows"]["wan-s2v"]["input_bindings"]["audio_file"] == {
        "node_id": "15",
        "field": "audio",
    }


def test_editing_models_are_configuration_only_and_never_downloaded() -> None:
    models = ContextCompiler().load_editing_models()

    assert models["download_policy"] == "never"
    assert models["artifact_policy"] == "externally-managed"
    assert models["visual_analyzer"]["model"] == "allenai/Molmo2-8B"
    assert models["editing_planner"]["model"] == (
        "Qwen/Qwen3-30B-A3B-Instruct-2507"
    )
    assert models["visual_analyzer"]["enabled"] is False
    assert models["audiovisual_analyzer"]["enabled"] is False
    assert models["audio_captioner"]["enabled"] is False
    assert models["editing_planner"]["output_schema"] == (
        "tools/schemas/edit-decision-list.schema.json"
    )
    assert models["lightweight_visual_analyzer"]["model"] == (
        "allenai/Molmo2-4B"
    )
    assert models["lightweight_editing_planner"]["model"] == (
        "Qwen/Qwen3-4B-Instruct-2507"
    )
    assert models["lightweight_transcriber"]["model"] == "whisper"
    assert models["lightweight_audio_classifier"]["model"] == "clap"
    assert all(
        not configuration["enabled"]
        for role, configuration in models.items()
        if role.startswith("lightweight_")
    )


def test_production_pipeline_dry_run_does_not_invoke_external_tools() -> None:
    plan = SceneGenerationPipeline(PROJECT_ROOT).produce_scene(
        STORY_ID,
        SCENE_ID,
        dry_run=True,
    )

    assert [
        (shot["shot_id"], shot["mode"], shot["workflow"])
        for shot in plan["shots"]
    ] == [
        ("shot-001", "t2v", "wan-t2v"),
        ("shot-002", "s2v", "wan-s2v"),
        ("shot-003", "i2v", "wan-i2v"),
        ("shot-004", "s2v", "wan-s2v"),
    ]
    assert plan["audio"]["ambience"]["tool"] == "ambience-generator"


def test_mcp_production_plan_uses_the_safe_dry_run() -> None:
    plan = plan_scene_production(STORY_ID, SCENE_ID)

    assert plan["project_id"] == "lpw"
    assert plan["scene_id"] == SCENE_ID


def test_real_production_requires_enabled_tools() -> None:
    with pytest.raises(ContextCompilerError, match="Required tool '.+' is disabled"):
        ContextCompiler().compile_production_scene(
            STORY_ID,
            SCENE_ID,
            require_enabled_tools=True,
        )


@pytest.mark.parametrize(
    ("duration", "fps", "expected"),
    [(5, 24, 117), (4, 24, 93), (3, 24, 69), (0, 24, 1)],
)
def test_frame_count_matches_wan_four_n_plus_one_constraint(
    duration: float,
    fps: int,
    expected: int,
) -> None:
    assert SceneGenerationPipeline._calculate_frame_count(duration, fps) == expected


def test_workflow_bindings_patch_the_exported_comfyui_document() -> None:
    workflow = {"6": {"inputs": {"text": "old"}}}

    SceneGenerationPipeline._apply_workflow_bindings(
        workflow,
        {"prompt": {"node_id": "6", "field": "text"}},
        {"prompt": "new prompt"},
    )

    assert workflow["6"]["inputs"]["text"] == "new prompt"


def test_output_directory_cannot_escape_project_root(tmp_path: Path) -> None:
    pipeline = SceneGenerationPipeline(PROJECT_ROOT)

    with pytest.raises(GenerationPipelineError, match="escapes project root"):
        pipeline._resolve_project_path(str(tmp_path), require_within_project=True)
