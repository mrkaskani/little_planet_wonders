from __future__ import annotations

import pytest

from lpw.context.compiler import ContextCompiler, ContextCompilerError
from lpw.context.pipeline import SceneContextPipeline


def test_scene_summary_matches_sample_hierarchy() -> None:
    summary = SceneContextPipeline().get_scene_summary(
        story_id="episode-001",
        scene_id="garden-discovery",
    )

    assert summary == {
        "project_id": "lpw",
        "story_id": "episode-001",
        "scene_id": "garden-discovery",
        "scene_title": "Garden Discovery",
        "location": "kindergarten_garden",
        "shot_count": 4,
        "prop_count": 2,
        "wardrobe_characters": ["riri", "yoyo"],
        "total_duration_seconds": 17,
        "generation_modes": ["t2v", "s2v", "i2v", "s2v"],
    }


def test_generation_plan_preserves_shot_order_and_inputs() -> None:
    plan = SceneContextPipeline().build_generation_plan(
        story_id="episode-001",
        scene_id="garden-discovery",
    )

    assert [
        (item["order"], item["shot_id"], item["generation_mode"], item["duration_seconds"])
        for item in plan
    ] == [
        (1, "shot-001", "t2v", 5),
        (2, "shot-002", "s2v", 4),
        (3, "shot-003", "i2v", 3),
        (4, "shot-004", "s2v", 5),
    ]
    assert plan[1]["speaker"] == "riri"
    assert plan[1]["audio_file"] == "assets/dialogue/shot-002-riri.wav"
    assert plan[2]["reference_image"] == "assets/keyframes/shot-003-yoyo.png"
    assert plan[1]["wardrobe"]["riri"]["id"] == "riri-primary"
    assert plan[2]["wardrobe"]["yoyo"]["id"] == "yoyo-primary"
    assert plan[2]["props"]["black-data-device"]["default_state"]["holder"] == "yoyo"
    assert plan[2]["continuity_before"]["props"]["black-data-device"]["condition"] == "active"
    assert plan[3]["continuity_after"]["characters"]["yoyo"]["emotional_state"] == "fearful-but-determined"


def test_compiled_scene_resolves_props_wardrobe_and_continuity() -> None:
    pipeline = SceneContextPipeline()
    context = pipeline.load_scene("episode-001", "garden-discovery")
    opening = pipeline.get_scene_opening_state(
        "episode-001", "garden-discovery"
    )
    expected_end = pipeline.get_scene_expected_end_state(
        "episode-001", "garden-discovery"
    )

    assert set(context["props"]) == {"black-data-device", "weapon"}
    assert set(context["wardrobe"]) == {"riri", "yoyo"}
    assert opening["props"]["black-data-device"]["holder"] == "yoyo"
    assert opening["props"]["weapon"]["condition"] == "secured"
    assert expected_end["characters"]["riri"]["emotional_state"] == "confrontational"


def test_context_compiler_rejects_paths_outside_context_data() -> None:
    with pytest.raises(ContextCompilerError, match="escapes the context root"):
        ContextCompiler().load_story("../../../outside")
