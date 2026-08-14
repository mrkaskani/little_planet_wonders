"""Validate the JSON contract used by the cloned-conversation generator."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConversationValidationError(ValueError):
    """Raised when a conversation JSON document is invalid."""


@dataclass(frozen=True)
class ConversationTurn:
    """One spoken turn in a conversation."""

    speaker: str
    text: str
    pause_after_seconds: float | None = None


@dataclass(frozen=True)
class ConversationSpec:
    """Validated conversation-generation settings and ordered turns."""

    title: str
    project: str
    language: str
    target_seconds: float
    seed: int
    turns: tuple[ConversationTurn, ...]

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "ConversationSpec":
        """Build a validated specification from decoded JSON data."""

        title = str(payload.get("title", "Conversation")).strip()
        project = str(payload.get("project", "classroom")).strip()
        language = str(payload.get("language", "English")).strip()
        target_seconds = payload.get("target_seconds", 30.0)
        seed = payload.get("seed", 424_242)
        raw_turns = payload.get("turns")
        if not title:
            raise ConversationValidationError("title must not be empty")
        if not project or "/" in project or ".." in project:
            raise ConversationValidationError("project must be a simple directory name")
        if not language:
            raise ConversationValidationError("language must not be empty")
        if not isinstance(target_seconds, (int, float)) or not 1 <= target_seconds <= 3600:
            raise ConversationValidationError("target_seconds must be between 1 and 3600")
        if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
            raise ConversationValidationError("seed must be a non-negative integer")
        if not isinstance(raw_turns, list) or not raw_turns:
            raise ConversationValidationError("turns must be a non-empty list")

        turns: list[ConversationTurn] = []
        for index, raw_turn in enumerate(raw_turns, start=1):
            if not isinstance(raw_turn, dict):
                raise ConversationValidationError(f"turn {index} must be an object")
            speaker = str(raw_turn.get("speaker", "")).strip().lower()
            text = str(raw_turn.get("text", "")).strip()
            pause = raw_turn.get("pause_after_seconds")
            if not speaker or "/" in speaker or ".." in speaker:
                raise ConversationValidationError(
                    f"turn {index} speaker must be a simple character id"
                )
            if not text:
                raise ConversationValidationError(f"turn {index} text must not be empty")
            if pause is not None and (
                not isinstance(pause, (int, float)) or not 0 <= pause <= 10
            ):
                raise ConversationValidationError(
                    f"turn {index} pause_after_seconds must be between 0 and 10"
                )
            turns.append(
                ConversationTurn(
                    speaker=speaker,
                    text=text,
                    pause_after_seconds=float(pause) if pause is not None else None,
                )
            )
        return cls(
            title=title,
            project=project,
            language=language,
            target_seconds=float(target_seconds),
            seed=seed,
            turns=tuple(turns),
        )


def load_conversation(path: Path) -> ConversationSpec:
    """Load and validate a conversation JSON file."""

    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ConversationValidationError(f"conversation JSON not found: {resolved}")
    try:
        payload = json.loads(resolved.read_text())
    except json.JSONDecodeError as exc:
        raise ConversationValidationError(f"invalid JSON in {resolved}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConversationValidationError("conversation JSON root must be an object")
    return ConversationSpec.from_mapping(payload)
