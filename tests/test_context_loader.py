from __future__ import annotations

import pytest

from little_planet_wonders.context.loader import load_project_context
from little_planet_wonders.errors import InvalidContextIdentifierError


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
