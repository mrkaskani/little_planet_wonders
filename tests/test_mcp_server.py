from __future__ import annotations

import asyncio

import yaml

from lpw.mcp.server import mcp
from lpw.mcp.resources import episode_context, location_context


def test_mcp_server_registers_one_cohesive_surface() -> None:
    async def inspect() -> tuple[list[str], list[str], list[str]]:
        tools = await mcp.list_tools()
        resources = await mcp.list_resources()
        templates = await mcp.list_resource_templates()
        return (
            [tool.name for tool in tools],
            [str(resource.uri) for resource in resources],
            [str(template.uri_template) for template in templates],
        )

    tool_names, resource_uris, resource_templates = asyncio.run(inspect())

    assert len(tool_names) == len(set(tool_names))
    assert "compile_cinematic_shot" in tool_names
    assert "inspect_episode_context" in tool_names
    assert "compile_scene_context" in tool_names
    assert "build_scene_generation_plan" in tool_names
    assert "plan_scene_production" in tool_names
    assert "plan_production_restoration" in tool_names
    assert "pipeline_system_status" in tool_names
    assert "validate_local_pipeline" in tool_names
    assert "run_production_preflight" in tool_names
    assert "create_render_attempt" in tool_names
    assert "validate_render_attempt" in tool_names
    assert "review_render_attempt" in tool_names
    assert "approve_render_attempt" in tool_names
    assert "reject_render_attempt" in tool_names
    assert "create_scene_release" in tool_names
    assert "render_wan_i2v_shot" in tool_names
    assert "finalize_cinematic_scene" in tool_names
    assert "approve_wan_render" in tool_names
    assert "prepare_automated_edit" in tool_names
    assert "automate_scene_edit" in tool_names
    assert "approve_edit_preview" in tool_names
    assert "post_edit_scene" in tool_names
    assert "resolve_context_chain" in tool_names
    assert "validate_context_chain" in tool_names
    assert "extend_cinematic_shot" in tool_names
    assert "compile_segment_context" in tool_names
    assert "approve_segment" in tool_names
    assert "prepare_exact_dialogue" in tool_names
    assert "lock_exact_dialogue" in tool_names
    assert "compile_dialogue_lip_sync_context" in tool_names
    assert "compile_sound_cue_sheet" in tool_names
    assert "compile_music_cue_sheet" in tool_names
    assert "validate_edit_plan" in tool_names
    assert "cinema://projects/{project_id}" in resource_templates
    assert "cinema://projects/{project_id}/episodes/{episode_id}" in resource_templates
    assert "cinema://studio/editing-models" in resource_uris
    assert "cinema://studio/wan22" in resource_uris
    assert "cinema://pipeline/models" in resource_uris
    assert "cinema://pipeline/environments/{environment}" in resource_templates
    assert "cinema://projects/{project_id}/audio" in resource_templates
    assert "cinema://projects/{project_id}/post-editing" in resource_templates
    assert (
        "cinema://projects/{project_id}/production-restoration"
        in resource_templates
    )
    assert "cinema://projects/{project_id}/export" in resource_templates
    assert "cinema://projects/{project_id}/continuity" in resource_templates
    assert (
        "cinema://projects/{project_id}/scenes/{scene_id}/edit-context"
        in resource_templates
    )
    assert (
        "cinema://projects/{project_id}/scenes/{scene_id}/prepared-package"
        in resource_templates
    )
    assert "cinema://stories/{story_id}/scenes/{scene_id}" in resource_templates
    assert "cinema://studio/{profile}" in resource_templates
    assert "cinema://projects/{project_id}/scenes/{scene_id}" in resource_templates
    assert "cinema://projects/{project_id}/shots/{shot_id}" in resource_templates
    assert "cinema://runtime/{segment_id}/end-state" in resource_templates
    assert "cinema://runtime/{scene_id}/audio-state" in resource_templates
    assert "cinema://runtime/{scene_id}/editing-state" in resource_templates
    assert "cinema://projects/{project_id}/voice-production" in resource_templates
    assert "cinema://projects/{project_id}/sound-effects" in resource_templates
    assert "cinema://projects/{project_id}/music" in resource_templates


def test_mcp_location_resource_resolves_versioned_candidate(context_root) -> None:
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
        "type: location-visual-version-context\n"
        "version: 2\n",
        encoding="utf-8",
    )

    result = yaml.safe_load(
        location_context("demo", "kindergarten-interior-location-v2")
    )

    assert result["id"] == "kindergarten-interior-location-v2"
    assert result["version"] == 2


def test_mcp_episode_resource_returns_resolved_character_emotion(context_root) -> None:
    project = context_root / "projects" / "demo"
    (project / "characters" / "riri" / "character.yaml").write_text(
        "id: riri\n"
        "identity:\n  name: Riri\n"
        "expression_library:\n"
        "  happy:\n"
        "    eyes: bright-and-soft\n"
        "    mouth: controlled-smile\n",
        encoding="utf-8",
    )
    (project / "characters" / "acting-style.yaml").write_text(
        "intensity_scale:\n  level_2:\n    name: clear\n"
        "emotion_contracts:\n"
        "  happiness:\n    maximum: clear\n"
        "character_performance_signatures:\n"
        "  riri:\n    emotional_baseline: warm\n",
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
        "    emotion:\n"
        "      id: happy\n"
        "      intensity: level_2\n"
        "      contract: happiness\n",
        encoding="utf-8",
    )

    result = yaml.safe_load(episode_context("demo", "episode-001"))

    assert result["episode"]["id"] == "episode-001"
    assert result["characters"][0]["character"]["identity"]["name"] == "Riri"
    assert result["characters"][0]["resolved_emotion"]["id"] == "happy"
    assert result["location"]["id"] == "kindergarten_garden"
