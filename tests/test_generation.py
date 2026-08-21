from __future__ import annotations

import pytest

from lpw.generation.compiler import (
    calculate_frame_count,
    compile_wan_shot_package,
)
from lpw.models import ShotRequest


def make_request(**overrides) -> ShotRequest:
    values = {
        "project_id": "demo",
        "shot_id": "shot-001",
        "scene_id": "scene-001",
        "character_ids": ["riri"],
        "location_id": "kindergarten_garden",
        "shot_type": "image_to_video",
        "action": "Riri turns toward the maintenance door.",
        "framing": "medium close-up",
        "lens": "85mm",
        "camera_height": "eye level",
        "camera_movement": "slow dolly-in",
        "start_frame": "keyframes/shot-001.png",
        "duration_seconds": 5,
    }
    values.update(overrides)
    return ShotRequest(**values)


def test_compiles_wan_package(context_root) -> None:
    package = compile_wan_shot_package(make_request(seed=42))

    assert package.model == "wan2.2-i2v-a14b"
    assert package.task == "i2v-A14B"
    assert package.frame_count == 117
    assert package.primary_reference_image == "keyframes/shot-001.png"
    assert "references/riri-three-quarter.png" in package.supporting_references
    assert "anime" in package.negative_prompt
    assert package.seed == 42
    assert len(package.package_hash) == 16


def test_frame_count_validation() -> None:
    assert calculate_frame_count(5, 24) == 117
    with pytest.raises(ValueError):
        calculate_frame_count(0)
