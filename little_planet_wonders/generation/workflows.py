from __future__ import annotations

from dataclasses import asdict
from typing import Any

from little_planet_wonders.config import workflows_root
from little_planet_wonders.generation.compiler import compile_wan_shot_package
from little_planet_wonders.models import ShotRequest
from little_planet_wonders.utils.files import load_json
from little_planet_wonders.utils.identifiers import validate_identifier


def prepare_generation_job(
    request: ShotRequest, workflow_name: str
) -> dict[str, Any]:
    """Load a verified ComfyUI workflow and pair it with a compiled shot."""

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
