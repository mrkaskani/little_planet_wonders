"""Define immutable defaults and supported values for this package."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_ROOT = PACKAGE_ROOT / "context_data"

PROJECT_FILE_NAME = "project.yaml"
STORIES_DIRECTORY_NAME = "stories"
SCENES_DIRECTORY_NAME = "scenes"
SHOTS_DIRECTORY_NAME = "shots"
PROPS_DIRECTORY_NAME = "props"
WARDROBE_DIRECTORY_NAME = "wardrobe"
CONTINUITY_DIRECTORY_NAME = "continuity"
TOOLS_DIRECTORY_NAME = "tools"
WORKFLOWS_DIRECTORY_NAME = "workflows"
PRODUCTION_DIRECTORY_NAME = "production"
VALIDATION_DIRECTORY_NAME = "validation"
VALIDATION_SCENES_DIRECTORY_NAME = "scenes"

GENERATION_TOOLS_FILE_NAME = "generation-tools.yaml"
EDITING_MODELS_FILE_NAME = "editing-models.yaml"
WAN_MODELS_FILE_NAME = "wan22-models.yaml"
VALIDATION_DEFAULTS_FILE_NAME = "defaults.yaml"

DEFAULT_RENDERS_DIRECTORY_NAME = "renders"

GENERATION_PACKAGE_FILE_NAME = "generation-package.json"
ATTEMPT_METADATA_FILE_NAME = "attempt-metadata.json"
VALIDATION_REPORT_FILE_NAME = "validation-report.json"
APPROVAL_FILE_NAME = "approval.json"

CONTEXT_SNAPSHOT_DIRECTORY_NAME = "context-snapshot"
COMPILED_CONTEXT_SNAPSHOT_FILE_NAME = "compiled-context.json"
VALIDATION_RULES_SNAPSHOT_FILE_NAME = "validation-rules.json"

RELEASES_DIRECTORY_NAME = "releases"
RELEASE_MANIFEST_FILE_NAME = "release-manifest.json"

DEFAULT_VIDEO_SETTINGS: dict[str, Any] = {
    "width": 1280,
    "height": 720,
    "fps": 24,
    "aspect_ratio": "16:9",
}

DEFAULT_CAMERA: dict[str, Any] = {
    "framing": "medium",
    "lens": "50mm",
    "angle": "eye-level",
    "movement": "locked",
    "screen_direction": "neutral",
}

DEFAULT_TRANSITION: dict[str, Any] = {
    "in": "cut",
    "out": "cut",
}

DEFAULT_GENERATION: dict[str, Any] = {
    "negative_prompt": "",
    "seed": None,
}

SUPPORTED_GENERATION_MODES: set[str] = {
    "t2v",
    "i2v",
    "ti2v",
    "s2v",
}

DIALOGUE_SHOT_TYPES: set[str] = {
    "dialogue",
    "narration",
}

SUPPORTED_TOOL_KINDS: set[str] = {
    "voice",
    "image",
    "video",
    "ambience",
    "sound-effect",
    "music",
    "lip-sync",
    "editor",
}

SUPPORTED_TOOL_TRANSPORTS: set[str] = {
    "http-json",
    "comfyui",
    "subprocess",
}

DEFAULT_TOOL_TIMEOUT_SECONDS = 600
DEFAULT_COMFYUI_POLL_INTERVAL_SECONDS = 2

SUPPORTED_VALIDATION_STATUSES: set[str] = {
    "pass",
    "fail",
    "warning",
    "pending",
    "not-applicable",
}

SUPPORTED_REVIEW_STATUSES: set[str] = {
    "pass",
    "fail",
    "not-applicable",
}
