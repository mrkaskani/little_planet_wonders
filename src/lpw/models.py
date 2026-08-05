from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ShotType = Literal[
    "draft",
    "text_to_video",
    "image_to_video",
    "dialogue",
    "performance",
]


@dataclass(frozen=True)
class ShotRequest:
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
    project_id: str
    scene_id: str
    shot_id: str
    character_id: str
    text: str
    emotion: str
    intensity: float = 0.5
    language: str = "Persian"
