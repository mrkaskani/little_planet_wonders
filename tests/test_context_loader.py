from __future__ import annotations

import pytest

from lpw.context.loader import (
    load_episode_context,
    load_project_context,
    load_voice,
)
from lpw.errors import InvalidContextDataError, InvalidContextIdentifierError


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
    assert "episode" not in first
    assert "episode_id" not in first["metadata"]
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


def test_loads_optional_five_second_reference_sequence_prompt(context_root) -> None:
    project = context_root / "projects" / "demo"
    prompt_directory = project / "generation-records" / "prompts"
    prompt_directory.mkdir(parents=True, exist_ok=True)
    (prompt_directory / "five-second-reference-sequence--s2v--prompt-v001.yaml").write_text(
        "id: demo-reference-sequence-prompt\n"
        "status: approved\n"
        "embedded_prompt_template: create-five-continuous-images\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["reference_sequence_prompt"]["id"] == (
        "demo-reference-sequence-prompt"
    )
    assert context["reference_sequence_prompt"]["embedded_prompt_template"] == (
        "create-five-continuous-images"
    )


def test_loads_optional_single_s2v_start_reference_prompt(context_root) -> None:
    project = context_root / "projects" / "demo"
    prompt_directory = project / "generation-records" / "prompts"
    prompt_directory.mkdir(parents=True, exist_ok=True)
    (prompt_directory / "single-start-reference--wan22-s2v--prompt-v003.yaml").write_text(
        "id: demo-single-start-reference-prompt\n"
        "status: approved\n"
        "embedded_positive_prompt_template: create-one-image\n"
        "embedded_negative_prompt: no-collage\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["s2v_start_reference_prompt"]["id"] == (
        "demo-single-start-reference-prompt"
    )
    assert context["s2v_start_reference_prompt"][
        "embedded_positive_prompt_template"
    ] == "create-one-image"
    assert context["s2v_start_reference_prompt"]["embedded_negative_prompt"] == (
        "no-collage"
    )


def test_loads_optional_s2v_dialogue_audio_prompt(context_root) -> None:
    project = context_root / "projects" / "demo"
    prompt_directory = project / "generation-records" / "prompts"
    prompt_directory.mkdir(parents=True, exist_ok=True)
    (prompt_directory / "s2v-dialogue-audio-preparation--prompt-v001.yaml").write_text(
        "id: demo-s2v-audio-prompt\n"
        "status: approved\n"
        "embedded_positive_prompt_template: add-clean-preroll\n"
        "embedded_negative_prompt: no-clipped-onset\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["s2v_dialogue_audio_prompt"]["id"] == "demo-s2v-audio-prompt"
    assert context["s2v_dialogue_audio_prompt"][
        "embedded_positive_prompt_template"
    ] == "add-clean-preroll"
    assert context["s2v_dialogue_audio_prompt"]["embedded_negative_prompt"] == (
        "no-clipped-onset"
    )


def test_loads_optional_s2v_runtime_profiles(context_root) -> None:
    project = context_root / "projects" / "demo"
    (project / "wan22-s2v-runtime-profiles.yaml").write_text(
        "id: demo-s2v-runtime-profiles\n"
        "profiles:\n"
        "  production: {model_precision: bf16}\n"
        "  local_m4_16gb: {model_precision: q4, model_format: gguf}\n",
        encoding="utf-8",
    )

    context = load_project_context("demo")

    assert context["s2v_runtime_profiles"]["profiles"]["production"][
        "model_precision"
    ] == "bf16"
    assert context["s2v_runtime_profiles"]["profiles"]["local_m4_16gb"] == {
        "model_precision": "q4",
        "model_format": "gguf",
    }


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


def test_resolves_versioned_location_candidate_by_exact_yaml_id(context_root) -> None:
    location = (
        context_root
        / "projects"
        / "demo"
        / "locations"
        / "interiors"
        / "location-v2.yaml"
    )
    location.parent.mkdir(parents=True, exist_ok=True)
    location.write_text(
        "id: kindergarten-interior-location-v2\n"
        "version: 2\n"
        "status: candidate\n",
        encoding="utf-8",
    )

    context = load_project_context(
        "demo", location_id="kindergarten-interior-location-v2"
    )

    assert context["location"]["id"] == "kindergarten-interior-location-v2"
    assert context["location"]["version"] == 2


def test_approved_v2_visual_authorities_overlay_base_context(context_root) -> None:
    project = context_root / "projects" / "demo"
    character_dir = project / "characters" / "riri"
    character_dir.mkdir(parents=True, exist_ok=True)
    (character_dir / "character.yaml").write_text(
        "id: riri\n"
        "personality:\n  primary_traits: [gentle]\n"
        "expression_library:\n"
        "  happy:\n"
        "    eyes: bright-and-soft\n"
        "    mouth: controlled-smile\n",
        encoding="utf-8",
    )
    (character_dir / "character-v2.yaml").write_text(
        "id: riri-character-v2\n"
        "version: 2\n"
        "version_tag: v002\n"
        "status: approved-canonical-v002\n"
        "versioning:\n  active_canonical_version: v002\n"
        "proportions:\n  total_height_head_units: 4.0\n",
        encoding="utf-8",
    )
    (project / "characters" / "acting-style.yaml").write_text(
        "intensity_scale:\n"
        "  level_2:\n"
        "    name: clear\n"
        "emotion_contracts:\n"
        "  happiness:\n"
        "    maximum: clear\n",
        encoding="utf-8",
    )

    location_dir = project / "locations" / "kindergarten_garden"
    location_dir.mkdir(parents=True, exist_ok=True)
    (location_dir / "location.yaml").write_text(
        "id: kindergarten_garden\n"
        "safety:\n  path: readable\n",
        encoding="utf-8",
    )
    (location_dir / "location-v2.yaml").write_text(
        "id: kindergarten-garden-location-v2\n"
        "version: 2\n"
        "version_tag: v002\n"
        "status: approved-canonical-v002\n"
        "metadata:\n  location_id: kindergarten_garden\n"
        "versioning:\n  active_canonical_version: v002\n"
        "location_identity:\n  summary: storybook-cottage-garden\n",
        encoding="utf-8",
    )

    episode = project / "episodes" / "episode-v2" / "episode.yaml"
    episode.parent.mkdir(parents=True, exist_ok=True)
    episode.write_text(
        "id: episode-v2\n"
        "location_id: kindergarten_garden\n"
        "characters:\n"
        "  - id: riri\n"
        "    emotion:\n"
        "      id: happy\n"
        "      intensity: level_2\n",
        encoding="utf-8",
    )

    context = load_project_context("demo", episode_id="episode-v2")

    character = context["characters"][0]
    assert character["id"] == "riri"
    assert character["proportions"]["total_height_head_units"] == 4.0
    assert character["expression_library"]["happy"]["eyes"] == "bright-and-soft"
    assert character["metadata"]["resolved_visual_version"] == "v002"
    assert context["episode"]["characters"][0]["resolved_emotion"]["id"] == "happy"
    assert context["location"]["id"] == "kindergarten_garden"
    assert context["location"]["location_identity"]["summary"] == "storybook-cottage-garden"
    assert context["location"]["safety"]["path"] == "readable"


def test_episode_resolves_character_emotion_and_default_location(context_root) -> None:
    project = context_root / "projects" / "demo"
    (project / "characters" / "riri" / "character.yaml").write_text(
        "id: riri\n"
        "identity:\n  name: Riri\n"
        "personality:\n  primary_traits: [gentle, cheerful]\n"
        "expression_library:\n"
        "  happy:\n"
        "    eyes: bright-and-soft\n"
        "    mouth: controlled-smile\n",
        encoding="utf-8",
    )
    (project / "characters" / "acting-style.yaml").write_text(
        "intensity_scale:\n"
        "  level_2:\n"
        "    name: clear\n"
        "    use: default-preschool-performance\n"
        "emotion_contracts:\n"
        "  happiness:\n"
        "    maximum: clear-with-brief-emphasis\n"
        "    require: controlled-smile\n"
        "character_performance_signatures:\n"
        "  riri:\n"
        "    emotional_baseline: warm-gentle-affectionate\n",
        encoding="utf-8",
    )
    episode = project / "episodes" / "episode-001" / "episode.yaml"
    episode.parent.mkdir(parents=True, exist_ok=True)
    episode.write_text(
        "id: episode-001\n"
        "type: episode-context\n"
        "version: 1\n"
        "location_id: kindergarten_garden\n"
        "characters:\n"
        "  - id: riri\n"
        "    episode_role: gentle-greeter\n"
        "    emotion:\n"
        "      id: happy\n"
        "      intensity: level_2\n"
        "      contract: happiness\n",
        encoding="utf-8",
    )

    resolved = load_episode_context(project, "episode-001")
    context = load_project_context("demo", episode_id="episode-001")

    riri = resolved["characters"][0]
    assert riri["character"]["identity"]["name"] == "Riri"
    assert riri["episode_state"]["episode_role"] == "gentle-greeter"
    assert riri["resolved_emotion"]["id"] == "happy"
    assert riri["resolved_emotion"]["expression"]["eyes"] == "bright-and-soft"
    assert riri["resolved_emotion"]["intensity_context"]["name"] == "clear"
    assert riri["resolved_emotion"]["contract"]["require"] == "controlled-smile"
    assert context["metadata"]["episode_id"] == "episode-001"
    assert context["metadata"]["character_ids"] == ["riri"]
    assert context["metadata"]["location_id"] == "kindergarten_garden"
    assert context["characters"][0]["id"] == "riri"
    assert context["location"]["id"] == "kindergarten_garden"
    assert context["episode"]["metadata"]["context_hash"]


def test_episode_rejects_unknown_character_expression(context_root) -> None:
    project = context_root / "projects" / "demo"
    (project / "characters" / "acting-style.yaml").write_text(
        "intensity_scale:\n  level_2:\n    name: clear\n"
        "emotion_contracts: {}\n",
        encoding="utf-8",
    )
    episode = project / "episodes" / "episode-002" / "episode.yaml"
    episode.parent.mkdir(parents=True, exist_ok=True)
    episode.write_text(
        "id: episode-002\n"
        "characters:\n"
        "  - id: riri\n"
        "    emotion:\n"
        "      id: angry\n"
        "      intensity: level_2\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidContextDataError, match="does not define"):
        load_episode_context(project, "episode-002")


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
