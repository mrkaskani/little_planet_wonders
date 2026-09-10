"""Plan quality-gated video restoration without invoking external model executors."""

from __future__ import annotations

from typing import Any

from lpw.context.loader import get_project_directory
from lpw.utils.files import load_yaml


ALLOWED_DEFECTS = {"face", "lip_sync", "temporal"}


def load_production_restoration(project_id: str) -> dict[str, Any]:
    """Load the authoritative restoration policy for a project.

    Args:
        project_id: Stable project identifier.

    Returns:
        Parsed production restoration policy.
    """

    return load_yaml(
        get_project_directory(project_id) / "production-restoration.yaml"
    )


def _validate_defects(defects: list[str]) -> list[str]:
    """Validate and de-duplicate requested defect classes.

    Args:
        defects: Defect classes reported by generated-video QA.

    Returns:
        Defect classes in their first-seen order.

    Raises:
        ValueError: If a defect does not have a configured repair route.
    """

    unknown = sorted(set(defects) - ALLOWED_DEFECTS)
    if unknown:
        raise ValueError(f"Unsupported restoration defect classes: {unknown}")
    return list(dict.fromkeys(defects))


def _executor_blockers(policy: dict[str, Any], stages: list[dict[str, Any]]) -> list[str]:
    """Return disabled executor requirements for the planned stages.

    Args:
        policy: Loaded restoration policy.
        stages: Ordered stage descriptions in the current plan.

    Returns:
        Human-readable requirements that block real execution.
    """

    executor_keys = {
        "qwen-input-qa": "qwen3_vl",
        "qwen-generated-video-qa": "qwen3_vl",
        "codeformer-face-repair": "codeformer",
        "latentsync-speaking-repair": "latentsync_1_6",
        "practical-rife-2x": "practical_rife",
        "seedvr2-restoration": "seedvr2",
        "qwen-final-comparative-qa": "qwen3_vl",
        "ffmpeg-master-and-delivery": "ffmpeg",
    }
    executors = policy.get("executors", {})
    blockers: list[str] = []
    for stage in stages:
        executor_key = executor_keys.get(stage["id"])
        if not executor_key:
            continue
        configuration = executors.get(executor_key, {})
        if not configuration.get("enabled", False):
            blocker = f"executor-not-enabled:{executor_key}"
            if blocker not in blockers:
                blockers.append(blocker)
    return blockers


def build_production_restoration_plan(
    policy: dict[str, Any],
    source_frames: str,
    hardware_profile: str,
    has_dialogue: bool,
    defects: list[str],
    difficult_scene: bool = False,
    available_vram_gb: float | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-executing restoration plan.

    Args:
        policy: Loaded production restoration policy.
        source_frames: Lossless source frame directory or immutable source identifier.
        hardware_profile: Named hardware profile from the policy.
        has_dialogue: Whether locked dialogue is present in the segment.
        defects: Structured defect classes produced by visual QA.
        difficult_scene: Whether to plan a per-segment ordering A/B test.
        available_vram_gb: Measured free VRAM before selecting SeedVR2.

    Returns:
        Ordered stages, routing decisions, downgrade record, and blockers.

    Raises:
        ValueError: If inputs conflict with the configured policy.
    """

    if not source_frames.strip():
        raise ValueError("source_frames must identify immutable lossless input frames")
    if available_vram_gb is not None and available_vram_gb < 0:
        raise ValueError("available_vram_gb cannot be negative")
    defects = _validate_defects(defects)
    profiles = policy.get("hardware_profiles", {})
    if hardware_profile not in profiles:
        raise ValueError(
            f"Unknown hardware profile {hardware_profile!r}; "
            f"expected one of {sorted(profiles)}"
        )
    if "lip_sync" in defects and not has_dialogue:
        raise ValueError("lip_sync repair requires locked dialogue audio")

    profile = profiles[hardware_profile]
    model_id = profile["seedvr2_model"]
    models = policy["restoration"]["model_priority"]
    selected = next((item for item in models if item["id"] == model_id), None)
    if selected is None:
        raise ValueError(f"Hardware profile selects unknown SeedVR2 model: {model_id}")

    stages: list[dict[str, Any]] = [
        {"id": "qwen-input-qa", "action": "stop-on-input-failure"},
        {
            "id": "wan22-s2v-a14b-generation",
            "action": "generate-native-candidate",
            "width": policy["pipeline"]["source_generation"]["native_width"],
            "height": policy["pipeline"]["source_generation"]["native_height"],
            "frame_rate": policy["pipeline"]["source_generation"]["native_frame_rate"],
        },
        {"id": "qwen-generated-video-qa", "action": "classify-bounded-defects"},
    ]
    repair_routes = {
        "face": ("codeformer-face-repair", "repair-face-region"),
        "lip_sync": ("latentsync-speaking-repair", "repair-speaking-mouth-motion"),
        "temporal": ("wan-bounded-segment-reprocess", "regenerate-padded-range"),
    }
    for defect in defects:
        stage_id, action = repair_routes[defect]
        stages.append(
            {
                "id": stage_id,
                "action": action,
                "defect": defect,
                "immutable_new_candidate": True,
            }
        )

    stages.extend(
        [
            {
                "id": "practical-rife-2x",
                "action": "interpolate-before-restoration",
                "multiplier": policy["interpolation"]["multiplier"],
            },
            {
                "id": "seedvr2-restoration",
                "action": "video-aware-temporal-restoration",
                "model": model_id,
                "precision": selected["precision"],
                "width": policy["restoration"]["output"]["width"],
                "height": policy["restoration"]["output"]["height"],
                "chunk_size_frames": policy["restoration"]["temporal_processing"][
                    "chunk_size_frames"
                ],
                "overlap_frames": policy["restoration"]["temporal_processing"][
                    "overlap_frames"
                ],
            },
            {"id": "ffmpeg-master-and-delivery", "action": "encode-and-validate"},
            {
                "id": "qwen-final-comparative-qa",
                "action": "compare-reference-pre-restoration-and-final",
            },
        ]
    )

    downgrade_record = None
    if selected["quality_rank"] > 1:
        downgrade_record = {
            "from": "seedvr2-7b-fp16",
            "to": model_id,
            "reason": f"selected-hardware-profile:{hardware_profile}",
            "available_vram_gb": available_vram_gb,
            "selected_precision": selected["precision"],
            "expected_quality_compromise": profile["expected_compromise"],
            "explicit": True,
        }

    if difficult_scene:
        ab_test = {
            "enabled": True,
            "scope": "difficult-segment-only",
            "candidate_a": policy["order_ab_test"]["default"],
            "candidate_b": policy["order_ab_test"]["alternate"],
            "selection": "qwen-comparison-plus-human-review",
        }
    else:
        ab_test = {
            "enabled": False,
            "selected_order": policy["order_ab_test"]["default"],
        }

    blockers = _executor_blockers(policy, stages)
    if downgrade_record is not None and available_vram_gb is None:
        blockers.append("available-vram-not-recorded-for-seedvr2-downgrade")
    return {
        "policy_id": policy["id"],
        "mode": "plan-only" if blockers else "ready-to-execute",
        "source": {
            "frames": source_frames,
            "required_format": policy["intermediates"]["frame_format"],
            "must_be_lossless": policy["intermediates"]["frame_lossless"],
            "immutable": True,
        },
        "hardware_profile": hardware_profile,
        "has_dialogue": has_dialogue,
        "defects": defects,
        "stages": stages,
        "ordering_ab_test": ab_test,
        "seedvr2_downgrade_record": downgrade_record,
        "candidate_policy": policy["intermediates"]["candidates"],
        "final_qa": policy["final_qa"],
        "completion_gates": policy["delivery"]["completion_gates"],
        "blocking_requirements": blockers,
    }


def plan_project_restoration(
    project_id: str,
    source_frames: str,
    hardware_profile: str,
    has_dialogue: bool,
    defects: list[str],
    difficult_scene: bool = False,
    available_vram_gb: float | None = None,
) -> dict[str, Any]:
    """Load project policy and build its non-executing restoration plan.

    Args:
        project_id: Stable project identifier.
        source_frames: Lossless source frame directory or immutable source identifier.
        hardware_profile: Named hardware profile from the project policy.
        has_dialogue: Whether locked dialogue is present in the segment.
        defects: Structured defect classes produced by visual QA.
        difficult_scene: Whether to plan a per-segment ordering A/B test.
        available_vram_gb: Measured free VRAM before selecting SeedVR2.

    Returns:
        Ordered restoration plan and any external executor blockers.
    """

    return build_production_restoration_plan(
        load_production_restoration(project_id),
        source_frames,
        hardware_profile,
        has_dialogue,
        defects,
        difficult_scene,
        available_vram_gb,
    )
