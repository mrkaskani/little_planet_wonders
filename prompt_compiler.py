"""Backward-compatible imports for cinematic prompt compilation."""

from little_planet_wonders.generation.compiler import (
    build_negative_prompt,
    build_positive_prompt,
    calculate_frame_count,
    compile_wan_shot_package,
    generate_stable_seed,
    select_primary_reference,
    select_wan_model,
)
from little_planet_wonders.generation.prompts import (
    DEFAULT_NEGATIVE_PROMPT,
    extract_negative_values,
    yaml_like_section,
)
from little_planet_wonders.models import ShotRequest, ShotType, WanShotPackage
from little_planet_wonders.utils.hashing import stable_hash as calculate_package_hash
from little_planet_wonders.utils.references import (
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
