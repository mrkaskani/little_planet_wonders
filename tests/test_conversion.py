"""Tests for the JSON cloned-conversation feature."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conversion.cli import find_workspace
from conversion.profiles import resolve_locked_voice
from conversion.schema import ConversationValidationError, load_conversation


def test_load_conversation_defaults_and_turn_pause(tmp_path: Path) -> None:
    source = tmp_path / "conversation.json"
    source.write_text(
        json.dumps(
            {
                "title": "Test",
                "turns": [
                    {"speaker": "YOYO", "text": " Hello. ", "pause_after_seconds": 0.4},
                    {"speaker": "riri", "text": "Hi!"},
                ],
            }
        )
    )

    spec = load_conversation(source)

    assert spec.project == "classroom"
    assert spec.language == "English"
    assert spec.target_seconds == 30
    assert spec.turns[0].speaker == "yoyo"
    assert spec.turns[0].text == "Hello."
    assert spec.turns[0].pause_after_seconds == 0.4


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"turns": []}, "non-empty"),
        ({"turns": [{"speaker": "../riri", "text": "Hi"}]}, "simple character id"),
        ({"turns": [{"speaker": "riri", "text": ""}]}, "text must not be empty"),
        ({"target_seconds": 0, "turns": [{"speaker": "riri", "text": "Hi"}]}, "between 1"),
    ],
)
def test_load_conversation_rejects_invalid_payload(
    tmp_path: Path,
    payload: dict[str, object],
    message: str,
) -> None:
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(payload))

    with pytest.raises(ConversationValidationError, match=message):
        load_conversation(source)


def test_resolve_locked_voice_from_profile(tmp_path: Path) -> None:
    project_root = tmp_path / "src/lpw/context/projects/classroom"
    profile = project_root / "characters/riri/voice-profile.yaml"
    audio = project_root / "audio-assets/voice-references/riri/neutral.wav"
    profile.parent.mkdir(parents=True)
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"locked voice")
    profile.write_text(
        "references:\n"
        "  neutral-friendly:\n"
        "    path: audio-assets/voice-references/riri/neutral.wav\n"
        "    text: Hello from Riri.\n"
    )

    reference = resolve_locked_voice(tmp_path, "classroom", "riri")

    assert reference.audio_path == audio
    assert reference.text == "Hello from Riri."
    assert len(reference.sha256) == 64


def test_find_workspace(tmp_path: Path) -> None:
    nested = tmp_path / "one/two"
    nested.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
    (tmp_path / "src/lpw").mkdir(parents=True)

    assert find_workspace(nested) == tmp_path
