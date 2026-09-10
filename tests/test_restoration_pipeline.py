"""Test production restoration routing, model selection, and safety gates."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from lpw.editing.restoration import (
    build_production_restoration_plan,
    load_production_restoration,
)
from lpw.mcp.resources import production_restoration_context
from lpw.mcp.tools import plan_production_restoration


POLICY_TEXT = """
id: demo-restoration
intermediates:
  frame_format: png
  frame_lossless: true
  candidates:
    immutable: true
restoration:
  output: {width: 1920, height: 1080}
  model_priority:
    - {id: seedvr2-7b-fp16, precision: fp16, quality_rank: 1}
    - {id: seedvr2-7b-quantized, precision: quantized, quality_rank: 3}
    - {id: seedvr2-3b-fallback, precision: reduced, quality_rank: 4}
  temporal_processing: {chunk_size_frames: 32, overlap_frames: 8}
pipeline:
  source_generation: {native_width: 832, native_height: 480, native_frame_rate: 16}
interpolation: {multiplier: 2}
order_ab_test:
  default: practical-rife-then-seedvr2
  alternate: seedvr2-then-practical-rife
hardware_profiles:
  production-high-memory:
    seedvr2_model: seedvr2-7b-fp16
    expected_compromise: none
  local-limited:
    seedvr2_model: seedvr2-7b-quantized
    expected_compromise: reduced-fine-texture
  emergency-low-memory:
    seedvr2_model: seedvr2-3b-fallback
    expected_compromise: reduced-restoration-capacity
executors:
  qwen3_vl: {enabled: false}
  codeformer: {enabled: false}
  latentsync_1_6: {enabled: false}
  practical_rife: {enabled: false}
  seedvr2: {enabled: false}
  ffmpeg: {enabled: true}
final_qa:
  reviewer: Qwen3-VL
delivery:
  completion_gates: [final-qa-pass, technical-validation-pass]
"""


def _policy() -> dict:
    """Return a compact valid policy fixture.

    Returns:
        Parsed restoration policy used by unit tests.
    """

    return yaml.safe_load(POLICY_TEXT)


def _write_policy(context_root: Path) -> Path:
    """Write the compact policy beneath the configured demo project.

    Args:
        context_root: Temporary configured context root.

    Returns:
        Path to the written project restoration policy.
    """

    path = context_root / "projects" / "demo" / "production-restoration.yaml"
    path.write_text(POLICY_TEXT, encoding="utf-8")
    return path


def test_routes_each_structured_defect_and_keeps_sources_immutable() -> None:
    plan = build_production_restoration_plan(
        _policy(),
        "/immutable/frames",
        "production-high-memory",
        True,
        ["face", "lip_sync", "temporal"],
    )

    stage_ids = [stage["id"] for stage in plan["stages"]]
    assert "codeformer-face-repair" in stage_ids
    assert "latentsync-speaking-repair" in stage_ids
    assert "wan-bounded-segment-reprocess" in stage_ids
    assert stage_ids.index("practical-rife-2x") < stage_ids.index(
        "seedvr2-restoration"
    )
    assert plan["source"]["must_be_lossless"] is True
    assert plan["source"]["immutable"] is True
    assert plan["seedvr2_downgrade_record"] is None


def test_rejects_lip_sync_repair_without_locked_dialogue() -> None:
    with pytest.raises(ValueError, match="requires locked dialogue"):
        build_production_restoration_plan(
            _policy(),
            "/immutable/frames",
            "production-high-memory",
            False,
            ["lip_sync"],
        )


def test_records_quantized_and_three_billion_parameter_downgrades() -> None:
    quantized = build_production_restoration_plan(
        _policy(), "/frames", "local-limited", False, [], available_vram_gb=12.5
    )
    fallback = build_production_restoration_plan(
        _policy(), "/frames", "emergency-low-memory", False, [], available_vram_gb=6.0
    )

    assert quantized["seedvr2_downgrade_record"] == {
        "from": "seedvr2-7b-fp16",
        "to": "seedvr2-7b-quantized",
        "reason": "selected-hardware-profile:local-limited",
        "available_vram_gb": 12.5,
        "selected_precision": "quantized",
        "expected_quality_compromise": "reduced-fine-texture",
        "explicit": True,
    }
    assert fallback["seedvr2_downgrade_record"]["to"] == "seedvr2-3b-fallback"
    assert fallback["seedvr2_downgrade_record"]["explicit"] is True


def test_missing_vram_measurement_blocks_a_downgraded_plan() -> None:
    plan = build_production_restoration_plan(
        _policy(), "/frames", "local-limited", False, []
    )

    assert plan["seedvr2_downgrade_record"]["available_vram_gb"] is None
    assert (
        "available-vram-not-recorded-for-seedvr2-downgrade"
        in plan["blocking_requirements"]
    )


def test_enables_order_ab_test_only_for_difficult_segment() -> None:
    normal = build_production_restoration_plan(
        _policy(), "/frames", "production-high-memory", False, []
    )
    difficult = build_production_restoration_plan(
        _policy(), "/frames", "production-high-memory", False, [], True
    )

    assert normal["ordering_ab_test"] == {
        "enabled": False,
        "selected_order": "practical-rife-then-seedvr2",
    }
    assert difficult["ordering_ab_test"]["enabled"] is True
    assert difficult["ordering_ab_test"]["scope"] == "difficult-segment-only"


def test_project_mcp_resource_and_tool_expose_policy_and_blockers(context_root) -> None:
    _write_policy(context_root)

    loaded = load_production_restoration("demo")
    resource = yaml.safe_load(production_restoration_context("demo"))
    plan = plan_production_restoration(
        "demo", "/immutable/frames", "local-limited", True, ["face"]
    )

    assert loaded["id"] == "demo-restoration"
    assert resource["id"] == "demo-restoration"
    assert plan["mode"] == "plan-only"
    assert "executor-not-enabled:qwen3_vl" in plan["blocking_requirements"]
    assert "executor-not-enabled:codeformer" in plan["blocking_requirements"]
    assert "executor-not-enabled:practical_rife" in plan["blocking_requirements"]
    assert "executor-not-enabled:seedvr2" in plan["blocking_requirements"]
