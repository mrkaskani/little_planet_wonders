"""Backward-compatible imports for cinematic prompt compilation."""

from lpw.generation.compiler import (
    build_negative_prompt,
    build_positive_prompt,
    calculate_frame_count,
    compile_wan_shot_package,
    generate_stable_seed,
    select_primary_reference,
    select_wan_model,
)
from lpw.generation.prompts import (
    DEFAULT_NEGATIVE_PROMPT,
    extract_negative_values,
    yaml_like_section,
)
from lpw.models import ShotRequest, ShotType, WanShotPackage
from lpw.utils.hashing import stable_hash as calculate_package_hash
from lpw.utils.references import (
    collect_reference_images as flatten_reference_images,
)

__all__ = [
    "DEFAULT_NEGATIVE_PROMPT",
    "ShotRequest",
    "ShotType",
    "WanShotPackage",
    "build_negative_prompt",
    "build_positive_prompt",
    "calculate_frame_count",
    "calculate_package_hash",
    "compile_wan_shot_package",
    "extract_negative_values",
    "flatten_reference_images",
    "generate_stable_seed",
    "select_primary_reference",
    "select_wan_model",
    "yaml_like_section",
]
