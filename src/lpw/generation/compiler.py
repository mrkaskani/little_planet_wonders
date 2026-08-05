"""Provide compiler services for the LPW cinematic pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from lpw.context.loader import load_project_context
from lpw.generation.prompts import (
    build_negative_prompt,
    build_positive_prompt,
)
from lpw.models import ShotRequest, WanShotPackage
from lpw.utils.hashing import stable_hash
from lpw.utils.references import collect_reference_images


def select_wan_model(request: ShotRequest) -> tuple[str, str]:
    """Select wan model.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.

    Returns:
        tuple[str, str]: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    if request.shot_type == "dialogue":
        if not request.dialogue_audio:
            raise ValueError("Dialogue shots require dialogue_audio.")
        return "wan2.2-s2v-14b", "s2v-14B"
    if request.shot_type == "performance":
        raise ValueError(
            "Wan Animate is intentionally excluded; use T2V, I2V, TI2V, or S2V."
        )
    models = {
        "draft": ("wan2.2-ti2v-5b", "ti2v-5B"),
        "image_to_video": ("wan2.2-i2v-a14b", "i2v-A14B"),
        "text_to_video": ("wan2.2-t2v-a14b", "t2v-A14B"),
    }
    try:
        return models[request.shot_type]
    except KeyError as error:
        raise ValueError(f"Unsupported shot type: {request.shot_type}") from error


def calculate_frame_count(duration_seconds: int, frame_rate: int = 24) -> int:
    """Calculate frame count.

    Args:
        duration_seconds (int): Requested duration in seconds.
        frame_rate (int): Frames per second used for timing calculations. Defaults to
            ``24``.

    Returns:
        int: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    if duration_seconds < 1:
        raise ValueError("duration_seconds must be at least 1.")
    if frame_rate < 1:
        raise ValueError("frame_rate must be at least 1.")
    requested_frames = duration_seconds * frame_rate
    return max(((requested_frames - 1) // 4) * 4 + 1, 5)


def select_primary_reference(
    request: ShotRequest, context: dict[str, Any]
) -> tuple[str | None, list[str]]:
    """Select primary reference.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.
        context (dict[str, Any]): Resolved cinematic context used by the operation.

    Returns:
        tuple[str | None, list[str]]: Result produced by the operation.
    """
    references = collect_reference_images(context)
    if request.start_frame:
        return request.start_frame, [item for item in references if item != request.start_frame]
    for character in context.get("characters", []):
        character_refs = character.get("reference_images", {})
        for key in (
            "shot_keyframe",
            "three_quarter",
            "face_three_quarter",
            "full_body",
            "face_front",
        ):
            reference = character_refs.get(key)
            if reference:
                reference = str(reference)
                return reference, [item for item in references if item != reference]
    return None, references


def generate_stable_seed(request: ShotRequest, context_hash: str) -> int:
    """Generate stable seed.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.
        context_hash (str): Context hash used by this operation.

    Returns:
        int: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    if request.seed is not None:
        if request.seed < 0:
            raise ValueError("seed cannot be negative.")
        return request.seed
    source = f"{request.project_id}:{request.scene_id}:{request.shot_id}:{context_hash}"
    return int(hashlib.sha256(source.encode("utf-8")).hexdigest()[:8], 16)


def compile_wan_shot_package(request: ShotRequest) -> WanShotPackage:
    """Compile wan shot package.

    Args:
        request (ShotRequest): Typed request containing the inputs for this operation.

    Returns:
        WanShotPackage: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    context = load_project_context(
        request.project_id,
        character_ids=request.character_ids,
        location_id=request.location_id,
    )
    context_hash = context["metadata"]["context_hash"]
    model, task = select_wan_model(request)
    primary_reference, supporting_references = select_primary_reference(request, context)
    if request.shot_type in {"image_to_video", "dialogue"} and not primary_reference:
        raise ValueError(
            f"{request.shot_type} requires a primary reference image or approved start frame."
        )
    frame_rate = int(
        context.get("project", {}).get("technical", {}).get(
            "frame_rate",
            context.get("studio", {}).get("generation", {}).get("frame_rate", 24),
        )
    )
    frame_count = calculate_frame_count(request.duration_seconds, frame_rate)
    seed = generate_stable_seed(request, context_hash)
    unsigned_package = {
        "request": asdict(request),
        "model": model,
        "task": task,
        "prompt": build_positive_prompt(request, context),
        "negative_prompt": build_negative_prompt(context),
        "primary_reference_image": primary_reference,
        "supporting_references": supporting_references,
        "size": "1280*704" if task == "ti2v-5B" else "1280*720",
        "frame_rate": frame_rate,
        "frame_count": frame_count,
        "seed": seed,
        "context_hash": context_hash,
    }
    return WanShotPackage(
        project_id=request.project_id,
        scene_id=request.scene_id,
        shot_id=request.shot_id,
        model=model,
        task=task,
        prompt=unsigned_package["prompt"],
        negative_prompt=unsigned_package["negative_prompt"],
        primary_reference_image=primary_reference,
        supporting_references=supporting_references,
        audio_path=request.dialogue_audio,
        performer_video=request.performer_video,
        size=unsigned_package["size"],
        frame_rate=frame_rate,
        duration_seconds=request.duration_seconds,
        frame_count=frame_count,
        seed=seed,
        context_hash=context_hash,
        package_hash=stable_hash(unsigned_package),
    )


__all__ = [
    "build_negative_prompt",
    "build_positive_prompt",
    "calculate_frame_count",
    "compile_wan_shot_package",
    "generate_stable_seed",
    "select_primary_reference",
    "select_wan_model",
]
