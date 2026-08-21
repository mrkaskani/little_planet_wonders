from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from lpw.generation.render_service import (
    WanRenderService,
    WanRenderServiceError,
    collect_output_descriptors,
    parse_size,
)
from lpw.generation.workflow_adapter import (
    WorkflowBindingError,
    apply_workflow_values,
    load_bindings,
    load_workflow,
)
from lpw.models import WanShotPackage


def _workflow() -> dict[str, Any]:
    specifications = [
        ("1", "MCP_POSITIVE_PROMPT", {"text": ""}),
        ("2", "MCP_NEGATIVE_PROMPT", {"text": ""}),
        ("3", "MCP_START_IMAGE", {"image": ""}),
        ("4", "MCP_HIGH_NOISE_SAMPLER", {"noise_seed": 0}),
        ("5", "MCP_LOW_NOISE_SAMPLER", {"noise_seed": 0}),
        (
            "6",
            "MCP_VIDEO_SETTINGS",
            {"length": 1, "width": 1, "height": 1},
        ),
        ("7", "MCP_OUTPUT", {"filename_prefix": ""}),
    ]
    return {
        node_id: {"inputs": inputs, "_meta": {"title": title}}
        for node_id, title, inputs in specifications
    }


def _bindings() -> dict[str, Any]:
    return {
        "positive_prompt": [{"title": "MCP_POSITIVE_PROMPT", "input": "text"}],
        "negative_prompt": [{"title": "MCP_NEGATIVE_PROMPT", "input": "text"}],
        "start_image": [{"title": "MCP_START_IMAGE", "input": "image"}],
        "seed": [
            {"title": "MCP_HIGH_NOISE_SAMPLER", "input": "noise_seed"},
            {"title": "MCP_LOW_NOISE_SAMPLER", "input": "noise_seed"},
        ],
        "frame_count": [{"title": "MCP_VIDEO_SETTINGS", "input": "length"}],
        "width": [{"title": "MCP_VIDEO_SETTINGS", "input": "width"}],
        "height": [{"title": "MCP_VIDEO_SETTINGS", "input": "height"}],
        "output_prefix": [{"title": "MCP_OUTPUT", "input": "filename_prefix"}],
    }


class FakeComfyUIClient:
    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok"}

    async def upload_image(self, image_path: Path) -> str:
        assert image_path.is_file()
        return "uploaded-reference.png"

    async def execute(
        self, workflow: dict[str, Any], *, timeout_seconds: float
    ) -> tuple[str, dict[str, Any]]:
        assert workflow["3"]["inputs"]["image"] == "uploaded-reference.png"
        assert timeout_seconds == 7200
        return (
            "prompt-001",
            {
                "outputs": {
                    "7": {
                        "videos": [
                            {
                                "filename": "wan-output.mp4",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                }
            },
        )

    async def download_output(
        self, descriptor: dict[str, Any], destination: Path
    ) -> Path:
        destination.write_bytes(b"generated-video")
        return destination


def test_semantic_workflow_bindings_are_applied_by_node_title(
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "workflow.json"
    bindings_path = tmp_path / "bindings.yaml"
    workflow_path.write_text(json.dumps(_workflow()), encoding="utf-8")
    bindings_path.write_text(yaml.safe_dump(_bindings()), encoding="utf-8")

    resolved = apply_workflow_values(
        load_workflow(workflow_path),
        load_bindings(bindings_path),
        {"positive_prompt": "cinematic rain", "seed": 42, "width": 1280},
    )

    assert resolved["1"]["inputs"]["text"] == "cinematic rain"
    assert resolved["4"]["inputs"]["noise_seed"] == 42
    assert resolved["5"]["inputs"]["noise_seed"] == 42
    assert resolved["6"]["inputs"]["width"] == 1280
    assert _workflow()["1"]["inputs"]["text"] == ""


def test_workflow_adapter_rejects_missing_semantic_node() -> None:
    with pytest.raises(WorkflowBindingError, match="No workflow node"):
        apply_workflow_values(
            {},
            {"seed": [{"title": "MCP_SAMPLER", "input": "seed"}]},
            {"seed": 1},
        )


def test_render_service_stores_reproducible_i2v_artifacts(tmp_path: Path) -> None:
    workflow_path = tmp_path / "workflow.json"
    bindings_path = tmp_path / "bindings.yaml"
    workflow_path.write_text(json.dumps(_workflow()), encoding="utf-8")
    bindings_path.write_text(yaml.safe_dump(_bindings()), encoding="utf-8")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"reference")
    package = WanShotPackage(
        project_id="lpw",
        scene_id="garden-discovery",
        shot_id="shot-003",
        model="wan2.2-i2v-a14b",
        task="i2v-A14B",
        prompt="cinematic rain",
        negative_prompt="artifacts",
        primary_reference_image=str(reference),
        supporting_references=[],
        audio_path=None,
        performer_video=None,
        size="1280*720",
        frame_rate=24,
        duration_seconds=3,
        frame_count=69,
        seed=42,
        context_hash="context123",
        package_hash="package123",
    )
    service = WanRenderService(
        FakeComfyUIClient(),
        workflow_file=workflow_path,
        bindings_file=bindings_path,
        render_root=tmp_path / "renders",
        project_root=tmp_path,
    )

    result = asyncio.run(service.render(package))

    render_directory = Path(result["render_directory"])
    assert result["status"] == "completed"
    assert (render_directory / "generation-package.json").is_file()
    assert (render_directory / "resolved-workflow.json").is_file()
    assert (render_directory / "comfy-history.json").is_file()
    assert (render_directory / "render-result.json").is_file()
    assert (render_directory / "output-00.mp4").read_bytes() == b"generated-video"
    with pytest.raises(FileExistsError):
        asyncio.run(service.render(package))


def test_disabled_project_comfyui_configuration_blocks_rendering() -> None:
    with pytest.raises(WanRenderServiceError, match="disabled"):
        WanRenderService.from_project_config()


def test_render_helpers_parse_dimensions_and_output_history() -> None:
    assert parse_size("1280×720") == (1280, 720)
    assert collect_output_descriptors(
        {"outputs": {"7": {"videos": [{"filename": "clip.mp4"}]}}}
    ) == [{"filename": "clip.mp4"}]
