"""Define typed request and package models used across LPW."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ShotType = Literal[
    "draft",
    "text_to_video",
    "image_to_video",
    "dialogue",
]


@dataclass(frozen=True)
class ShotRequest:
    """Represent ShotRequest behavior in the LPW pipeline.

    Attributes:
        project_id (str): Stored project id value.
        shot_id (str): Stored shot id value.
        scene_id (str): Stored scene id value.
        character_ids (list[str]): Stored character ids value.
        location_id (str): Stored location id value.
        shot_type (ShotType): Stored shot type value.
        action (str): Stored action value.
        framing (str): Stored framing value.
        lens (str): Stored lens value.
        camera_height (str): Stored camera height value.
        camera_movement (str): Stored camera movement value.
        emotional_tone (str): Stored emotional tone value.
        dialogue_audio (str | None): Stored dialogue audio value.
        start_frame (str | None): Stored start frame value.
        performer_video (str | None): Optional pose-conditioning video for S2V; it
            never enables Wan Animate.
        duration_seconds (int): Stored duration seconds value.
        seed (int | None): Stored seed value.
    """
    project_id: str
    shot_id: str
    scene_id: str
    character_ids: list[str]
    location_id: str
    shot_type: ShotType
    action: str
    framing: str
    lens: str
    camera_height: str
    camera_movement: str
    emotional_tone: str = ""
    dialogue_audio: str | None = None
    start_frame: str | None = None
    performer_video: str | None = None
    duration_seconds: int = 5
    seed: int | None = None


@dataclass(frozen=True)
class WanShotPackage:
    """Represent WanShotPackage behavior in the LPW pipeline.

    Attributes:
        project_id (str): Stored project id value.
        scene_id (str): Stored scene id value.
        shot_id (str): Stored shot id value.
        model (str): Stored model value.
        task (str): Stored task value.
        prompt (str): Stored prompt value.
        negative_prompt (str): Stored negative prompt value.
        primary_reference_image (str | None): Stored primary reference image value.
        supporting_references (list[str]): Stored supporting references value.
        audio_path (str | None): Stored audio path value.
        performer_video (str | None): Stored performer video value.
        size (str): Stored size value.
        frame_rate (int): Stored frame rate value.
        duration_seconds (int): Stored duration seconds value.
        frame_count (int): Stored frame count value.
        seed (int): Stored seed value.
        context_hash (str): Stored context hash value.
        package_hash (str): Stored package hash value.
    """
    project_id: str
    scene_id: str
    shot_id: str
    model: str
    task: str
    prompt: str
    negative_prompt: str
    primary_reference_image: str | None
    supporting_references: list[str]
    audio_path: str | None
    performer_video: str | None
    size: str
    frame_rate: int
    duration_seconds: int
    frame_count: int
    seed: int
    context_hash: str
    package_hash: str


@dataclass(frozen=True)
class DialogueRequest:
    """Represent DialogueRequest behavior in the LPW pipeline.

    Attributes:
        project_id (str): Stored project id value.
        scene_id (str): Stored scene id value.
        shot_id (str): Stored shot id value.
        character_id (str): Stored character id value.
        text (str): Stored text value.
        emotion (str): Stored emotion value.
        intensity (float): Stored intensity value.
        language (str): Stored language value.
    """
    project_id: str
    scene_id: str
    shot_id: str
    character_id: str
    text: str
    emotion: str
    intensity: float = 0.5
    language: str = "Persian"
