from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lpw.config import PROJECT_ROOT, renders_root, workflows_root
from lpw.context.compiler import ContextCompiler
from lpw.context.defaults import DEFAULT_CONTEXT_ROOT
from lpw.integrations.comfyui import ComfyUIClient
from lpw.models import WanShotPackage
from lpw.utils.files import atomic_write_json
from lpw.utils.identifiers import validate_identifier
from lpw.generation.workflow_adapter import (
    apply_workflow_values,
    load_bindings,
    load_workflow,
)


class WanRenderServiceError(RuntimeError):
    """Raised when an I2V render cannot be prepared or stored safely."""


def parse_size(size: str) -> tuple[int, int]:
    parts = size.lower().replace("×", "x").replace("*", "x").split("x")
    if len(parts) != 2:
        raise ValueError(f"Unsupported size format: {size}")
    width, height = (int(part.strip()) for part in parts)
    if width < 1 or height < 1:
        raise ValueError("Render dimensions must be positive.")
    return width, height


def collect_output_descriptors(history: dict[str, Any]) -> list[dict[str, Any]]:
    descriptors: list[dict[str, Any]] = []
    for node_output in history.get("outputs", {}).values():
        if not isinstance(node_output, dict):
            continue
        for output_value in node_output.values():
            if not isinstance(output_value, list):
                continue
            descriptors.extend(
                item
                for item in output_value
                if isinstance(item, dict) and item.get("filename")
            )
    return descriptors


class WanRenderService:
    """Resolve semantic bindings and execute one Wan I2V package in ComfyUI."""

    def __init__(
        self,
        client: ComfyUIClient,
        *,
        workflow_file: Path,
        bindings_file: Path,
        render_root: Path,
        project_root: Path = PROJECT_ROOT,
    ) -> None:
        self._client = client
        self._workflow_file = workflow_file.expanduser().resolve()
        self._bindings_file = bindings_file.expanduser().resolve()
        self._render_root = render_root.expanduser().resolve()
        self._project_root = project_root.expanduser().resolve()

    @classmethod
    def from_project_config(cls) -> WanRenderService:
        compiler = ContextCompiler()
        tool = compiler.load_generation_tools()["wan22-comfyui"]
        if not tool["enabled"]:
            raise WanRenderServiceError(
                "ComfyUI rendering is disabled in generation-tools.yaml."
            )
        settings = tool["settings"]
        workflow = compiler.load_workflow("wan-i2v")
        binding_value = workflow.get("semantic_bindings_file")
        if not isinstance(binding_value, str) or not binding_value:
            raise WanRenderServiceError(
                "wan-i2v workflow requires semantic_bindings_file."
            )
        workflow_value = Path(workflow["api_workflow_file"])
        if workflow_value.is_absolute():
            workflow_file = workflow_value
        elif workflow_value.parts and workflow_value.parts[0] == "workflows":
            workflow_file = workflows_root().joinpath(*workflow_value.parts[1:])
        else:
            workflow_file = PROJECT_ROOT / workflow_value
        return cls(
            ComfyUIClient(
                settings["base_url"],
                request_timeout_seconds=float(
                    settings.get("timeout_seconds", 60)
                ),
                poll_interval_seconds=float(
                    settings.get("poll_interval_seconds", 1)
                ),
            ),
            workflow_file=workflow_file,
            bindings_file=DEFAULT_CONTEXT_ROOT / binding_value,
            render_root=renders_root(),
        )

    async def render(self, package: WanShotPackage) -> dict[str, Any]:
        if package.task != "i2v-A14B":
            raise WanRenderServiceError(
                f"This integration only supports i2v-A14B, received: {package.task}"
            )
        project_id = validate_identifier(package.project_id, "project_id")
        scene_id = validate_identifier(package.scene_id, "scene_id")
        shot_id = validate_identifier(package.shot_id, "shot_id")
        package_hash = validate_identifier(package.package_hash, "package_hash")
        workflow_template = load_workflow(self._workflow_file)
        bindings = load_bindings(self._bindings_file)

        render_directory = (
            self._render_root / project_id / scene_id / shot_id / package_hash
        ).resolve()
        try:
            render_directory.relative_to(self._render_root)
        except ValueError as error:
            raise WanRenderServiceError("Render path escapes render storage.") from error
        render_directory.mkdir(parents=True, exist_ok=False)
        atomic_write_json(
            render_directory / "generation-package.json", asdict(package)
        )

        try:
            await self._client.health_check()
            if not package.primary_reference_image:
                raise WanRenderServiceError(
                    "I2V rendering requires a primary reference image."
                )
            reference = Path(package.primary_reference_image).expanduser()
            if not reference.is_absolute():
                reference = self._project_root / reference
            uploaded_image = await self._client.upload_image(reference.resolve())
            width, height = parse_size(package.size)
            values = {
                "positive_prompt": package.prompt,
                "negative_prompt": package.negative_prompt,
                "start_image": uploaded_image,
                "seed": package.seed,
                "frame_count": package.frame_count,
                "width": width,
                "height": height,
                "output_prefix": (
                    f"{project_id}_{scene_id}_{shot_id}_{package_hash}"
                ),
            }
            resolved_workflow = apply_workflow_values(
                workflow_template, bindings, values
            )
            atomic_write_json(
                render_directory / "resolved-workflow.json", resolved_workflow
            )
            prompt_id, history = await self._client.execute(
                resolved_workflow, timeout_seconds=7200
            )
            atomic_write_json(render_directory / "comfy-history.json", history)
            descriptors = collect_output_descriptors(history)
            if not descriptors:
                raise WanRenderServiceError(
                    "ComfyUI completed without any downloadable output descriptor."
                )
            outputs = []
            for index, descriptor in enumerate(descriptors):
                extension = Path(str(descriptor["filename"])).suffix or ".bin"
                destination = render_directory / f"output-{index:02d}{extension}"
                downloaded = await self._client.download_output(
                    descriptor, destination
                )
                outputs.append(str(downloaded))
            result = {
                "status": "completed",
                "project_id": project_id,
                "scene_id": scene_id,
                "shot_id": shot_id,
                "task": package.task,
                "prompt_id": prompt_id,
                "context_hash": package.context_hash,
                "package_hash": package_hash,
                "render_directory": str(render_directory),
                "outputs": outputs,
            }
            atomic_write_json(render_directory / "render-result.json", result)
            return result
        except Exception as error:
            atomic_write_json(
                render_directory / "render-error.json",
                {
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "message": str(error),
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                },
            )
            raise


async def render_wan_package(package: WanShotPackage) -> dict[str, Any]:
    """Render using the disabled-by-default project ComfyUI configuration."""

    return await WanRenderService.from_project_config().render(package)
