from __future__ import annotations

import pytest

from lpw.context.loader import load_project_context, load_voice
from lpw.errors import InvalidContextIdentifierError


def test_loads_nested_context_schema_and_stable_hash(context_root) -> None:
    first = load_project_context(
        "demo", character_ids=["riri"], location_id="kindergarten_garden"
    )
    second = load_project_context(
        "demo", character_ids=["riri"], location_id="kindergarten_garden"
    )

    assert first["characters"][0]["id"] == "riri"
    assert first["location"]["id"] == "kindergarten_garden"
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


def test_prefers_canonical_palette_and_loads_wan_preproduction_contract(
    context_root,
) -> None:
    project = context_root / "projects" / "demo"
    (project / "visual_style" / "palette-v2.yaml").write_text(
        "id: demo-palette-v2\nstatus: approved\nmetadata:\n  canonical: true\n",
        encoding="utf-8",
    )
    (project / "wan22-preproduction.yaml").write_text(
        "id: demo-wan22\nstatus: approved\nsupported_tasks:\n  t2v: {}\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["color_palette"]["id"] == "demo-palette-v2"
    assert context["color_palette"]["metadata"]["canonical"] is True
    assert context["wan_2_2"]["id"] == "demo-wan22"


def test_resolves_location_by_canonical_yaml_id_when_folder_name_differs(
    context_root,
) -> None:
    location = (
        context_root
        / "projects"
        / "demo"
        / "locations"
        / "exteriors"
        / "location.yaml"
    )
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        "id: kindergarten-exterior\nmetadata:\n  folder_id: exteriors\n",
        encoding="utf-8",
    )

    context = load_project_context("demo", location_id="kindergarten-exterior")

    assert context["location"]["id"] == "kindergarten-exterior"


def test_loads_schema_first_prop_catalog(context_root) -> None:
    catalog = context_root / "projects" / "demo" / "assets" / "props.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        "id: demo-prop-catalog\nstatus: approved-schema\nregistry: []\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["prop_catalog"]["id"] == "demo-prop-catalog"
    assert context["prop_catalog"]["registry"] == []


def test_loads_schema_first_costume_catalog(context_root) -> None:
    catalog = context_root / "projects" / "demo" / "assets" / "costumes.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        "id: demo-costume-catalog\nstatus: approved-schema\nregistry: []\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["costume_catalog"]["id"] == "demo-costume-catalog"
    assert context["costume_catalog"]["registry"] == []


def test_loads_schema_first_vehicle_catalog(context_root) -> None:
    catalog = context_root / "projects" / "demo" / "assets" / "vehicles.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        "id: demo-vehicle-catalog\nstatus: approved-schema\nregistry: []\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["vehicle_catalog"]["id"] == "demo-vehicle-catalog"
    assert context["vehicle_catalog"]["registry"] == []


def test_loads_preproduction_governance_and_background_catalog(context_root) -> None:
    project = context_root / "projects" / "demo"
    files = {
        "brand.yaml": "id: demo-brand\n",
        "references.yaml": "id: demo-references\n",
        "reference-views.yaml": "id: demo-reference-views\n",
        "asset-conventions.yaml": "id: demo-asset-conventions\n",
        "safety.yaml": "id: demo-safety\n",
        "educational-direction.yaml": "id: demo-education\n",
        "preproduction-checklist.yaml": "id: demo-checklist\n",
        "wan22-review-cards.yaml": "id: demo-review-cards\n",
        "characters/animation-style.yaml": "id: demo-animation\n",
        "characters/acting-style.yaml": "id: demo-acting\n",
        "characters/relationships.yaml": "id: demo-relationships\n",
        "assets/background-characters.yaml": (
            "id: demo-background-catalog\nregistry: []\n"
        ),
        "audios/voice-reference-audit.yaml": "id: demo-voice-audit\n",
    }
    for relative, content in files.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    context = load_project_context("demo")

    assert context["brand"]["id"] == "demo-brand"
    assert context["references"]["id"] == "demo-references"
    assert context["animation_style"]["id"] == "demo-animation"
    assert context["background_character_catalog"]["registry"] == []
    assert context["audio_context"]["voice_reference_audit"]["id"] == "demo-voice-audit"


def test_character_local_voice_profile_takes_precedence(context_root) -> None:
    profile = (
        context_root
        / "projects"
        / "demo"
        / "characters"
        / "riri"
        / "voice-profile.yaml"
    )
    profile.write_text(
        "id: riri\n"
        "voice_identity:\n"
        "  apparent_age: young child\n"
        "generation:\n"
        "  voice_id: riri-local-v1\n",
        encoding="utf-8",
    )

    voice = load_voice("demo", "riri")

    assert voice["id"] == "riri"
    assert voice["generation"]["voice_id"] == "riri-local-v1"
