from __future__ import annotations

import pytest

from lpw.context.loader import load_project_context, load_voice
from lpw.errors import InvalidContextIdentifierError


def test_loads_nested_context_schema_and_stable_hash(context_root) -> None:
    first = load_project_context(
        "demo", character_ids=["roxana"], location_id="rooftop"
    )
    second = load_project_context(
        "demo", character_ids=["roxana"], location_id="rooftop"
    )

    assert first["characters"][0]["id"] == "roxana"
    assert first["location"]["id"] == "rooftop"
    assert first["camera_language"]["camera_language"]["closeup"]["lens"] == "85mm"
    assert first["continuity"]["visual_state"]["time_of_day"] == "night"
    assert first["metadata"]["context_hash"] == second["metadata"]["context_hash"]
    assert len(first["metadata"]["context_hash"]) == 16


def test_rejects_path_traversal(context_root) -> None:
    with pytest.raises(InvalidContextIdentifierError):
        load_project_context("../../secret")


def test_audio_context_changes_the_project_hash(context_root) -> None:
    before = load_project_context("demo")["metadata"]["context_hash"]
    continuity = (
        context_root
        / "projects"
        / "demo"
        / "audios"
        / "audio-continuity.yaml"
    )
    continuity.write_text(
        "music:\n  active_cue: resolution-theme-01\n  intensity: 0.2\n",
        encoding="utf-8",
    )

    after = load_project_context("demo")["metadata"]["context_hash"]

    assert after != before


def test_character_local_voice_profile_takes_precedence(context_root) -> None:
    profile = (
        context_root
        / "projects"
        / "demo"
        / "characters"
        / "roxana"
        / "voice-profile.yaml"
    )
    profile.write_text(
        "id: roxana\n"
        "voice_identity:\n"
        "  apparent_age: young child\n"
        "generation:\n"
        "  voice_id: roxana-local-v1\n",
        encoding="utf-8",
    )

    voice = load_voice("demo", "roxana")

    assert voice["id"] == "roxana"
    assert voice["generation"]["voice_id"] == "roxana-local-v1"
