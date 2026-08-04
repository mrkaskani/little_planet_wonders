from __future__ import annotations

import json
from pathlib import Path

import yaml

from little_planet_wonders.editing.planner import create_edit_plan
from little_planet_wonders.editing.state import save_continuity_state
from little_planet_wonders.editing.validation import validate_edit_plan


def _metadata(path: Path, shot_id: str, direction: str) -> None:
    path.write_text(
        json.dumps(
            {
                "shot_id": shot_id,
                "camera": {"screen_direction": direction, "shot_size": "close-up"},
                "visual_state": {
                    "weather": "rain",
                    "time_of_day": "night",
                    "lighting_state": "cold-moonlight",
                    "grade_reference": "shot-001",
                },
                "character_state": {
                    "roxana": {
                        "position": "center",
                        "looking_direction": "camera-left",
                        "wardrobe": "burgundy-jacket",
                        "held_objects": ["data-device"],
                    }
                },
                "edit": {"preferred_in_frame": 0, "preferred_out_frame": 100},
            }
        ),
        encoding="utf-8",
    )


def test_edit_plan_and_continuity_validation(context_root, tmp_path: Path) -> None:
    first = tmp_path / "shot-001.json"
    second = tmp_path / "shot-002.json"
    _metadata(first, "shot-001", "left-to-right")
    _metadata(second, "shot-002", "right-to-left")

    plan = create_edit_plan("demo", [str(first), str(second)], "shot-001")
    result = validate_edit_plan(plan)

    assert result["blocking_errors"] == []
    assert any("screen-direction" in warning for warning in result["warnings"])
    assert plan["shots"][0]["normalization"]["resolution"] == "1920x804"


def test_missing_required_source_blocks_render(context_root, tmp_path: Path) -> None:
    metadata = tmp_path / "shot.json"
    _metadata(metadata, "shot-001", "left-to-right")
    content = json.loads(metadata.read_text(encoding="utf-8"))
    content["video_path"] = str(tmp_path / "missing.mp4")
    metadata.write_text(json.dumps(content), encoding="utf-8")

    plan = create_edit_plan(
        "demo", [str(metadata)], "shot-001", require_existing_sources=True
    )
    result = validate_edit_plan(plan)

    assert any("does not exist" in error for error in result["blocking_errors"])


def test_continuity_state_is_written_outside_context(
    context_root, tmp_path: Path, monkeypatch
) -> None:
    runtime = tmp_path / "runtime"
    monkeypatch.setenv("CINEMATIC_RUNTIME_ROOT", str(runtime))
    last_shot = {
        "shot_id": "shot-012",
        "camera": {"screen_direction": "left-to-right", "shot_size": "close-up"},
        "visual_state": {
            "grade_reference": "shot-001",
            "lighting_state": "cold-moonlight",
        },
        "character_state": {"roxana": {"wardrobe": "burgundy-jacket"}},
    }

    saved = Path(save_continuity_state("demo", "scene-001", 4, last_shot))
    content = yaml.safe_load(saved.read_text(encoding="utf-8"))

    assert context_root not in saved.parents
    assert content["edit_version"] == 4
    assert content["last_shot"]["id"] == "shot-012"
