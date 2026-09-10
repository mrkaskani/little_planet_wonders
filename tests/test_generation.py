from __future__ import annotations

import pytest

from lpw.generation.compiler import (
    calculate_frame_count,
    calculate_s2v_infer_frames,
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


def test_s2v_uses_native_480p_profile_and_exact_five_second_coverage(
    context_root,
) -> None:
    package = compile_wan_shot_package(
        make_request(
            shot_type="dialogue",
            dialogue_audio="audio/locked-dialogue.wav",
        )
    )

    assert package.model == "wan2.2-s2v-14b"
    assert package.task == "s2v-14B"
    assert package.size == "832*480"
    assert package.frame_rate == 16
    assert package.frame_count == 81
    assert package.supporting_references == []


def test_s2v_frame_count_rounds_up_to_cover_complete_audio() -> None:
    assert calculate_s2v_infer_frames(5, 16) == 81
    assert calculate_s2v_infer_frames(5.01, 16) == 85
    assert calculate_s2v_infer_frames(1.25, 16) == 21
    assert calculate_s2v_infer_frames(1.5, 16) == 25
    with pytest.raises(ValueError):
        calculate_s2v_infer_frames(0, 16)
