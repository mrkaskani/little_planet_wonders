"""Provide workflows services for the LPW cinematic pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from lpw.config import workflows_root
from lpw.generation.compiler import compile_wan_shot_package
from lpw.models import ShotRequest
from lpw.utils.files import load_json
from lpw.utils.identifiers import validate_identifier


def prepare_generation_job(
    request: ShotRequest, workflow_name: str
) -> dict[str, Any]:
    """Load a verified ComfyUI workflow and pair it with a compiled shot.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.
        workflow_name (str): Workflow name used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    workflow_name = validate_identifier(workflow_name, "workflow_name")
    workflow_path = workflows_root() / f"{workflow_name}.json"
    package = compile_wan_shot_package(request)
    return {
        "workflow": load_json(workflow_path),
        "shot": asdict(package),
        "bindings": {
            "positive_prompt": package.prompt,
            "negative_prompt": package.negative_prompt,
            "reference_images": [
                item
                for item in [package.primary_reference_image, *package.supporting_references]
                if item
            ],
            "context_hash": package.context_hash,
        },
    }
