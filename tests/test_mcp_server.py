from __future__ import annotations

import asyncio

import yaml

from lpw.mcp.server import mcp
from lpw.mcp.resources import location_context


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
    assert "compile_scene_context" in tool_names
    assert "build_scene_generation_plan" in tool_names
    assert "plan_scene_production" in tool_names
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
    assert "cinema://studio/editing-models" in resource_uris
    assert "cinema://studio/wan22" in resource_uris
    assert "cinema://projects/{project_id}/audio" in resource_templates
    assert "cinema://projects/{project_id}/post-editing" in resource_templates
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
