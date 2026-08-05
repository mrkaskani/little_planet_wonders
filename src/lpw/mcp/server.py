"""Expose the compatibility entry point for the LPW MCP server."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from lpw.mcp import resources, tools


mcp = MCPServer(
    "Little Planet Wonders",
    instructions=(
        "Compile cinematic generation and editing plans from project context. "
        "Use edit_cinematic_sequence before rendering edits, preserve continuity, "
        "and reject plans with blocking validation errors."
    ),
)

mcp.resource("cinema://studio")(resources.studio_context)
mcp.resource("cinema://studio/{profile}")(resources.studio_profile)
mcp.resource("cinema://studio/editing-models")(resources.editing_models_context)
mcp.resource("cinema://studio/wan22")(resources.wan22_context)
mcp.resource("cinema://projects/{project_id}")(resources.project_context)
mcp.resource("cinema://projects/{project_id}/characters/{character_id}")(
    resources.character_context
)
mcp.resource("cinema://projects/{project_id}/locations/{location_id}")(
    resources.location_context
)
mcp.resource("cinema://projects/{project_id}/audio")(resources.project_audio_context)
mcp.resource("cinema://projects/{project_id}/voices/{character_id}")(
    resources.character_voice_context
)
mcp.resource("cinema://projects/{project_id}/voice-production")(
    resources.voice_production_context
)
mcp.resource("cinema://projects/{project_id}/sound-effects")(
    resources.sound_effects_context
)
mcp.resource("cinema://projects/{project_id}/music")(resources.music_context)
mcp.resource("cinema://projects/{project_id}/editing")(resources.editing_context)
mcp.resource("cinema://projects/{project_id}/post-editing")(
    resources.post_editing_context
)
mcp.resource("cinema://projects/{project_id}/export")(resources.export_context)
mcp.resource("cinema://projects/{project_id}/continuity")(
    resources.continuity_context
)
mcp.resource("cinema://projects/{project_id}/scenes/{scene_id}/edit-context")(
    resources.scene_editing_context
)
mcp.resource("cinema://projects/{project_id}/scenes/{scene_id}/prepared-package")(
    resources.prepared_editing_package
)
mcp.resource("cinema://stories/{story_id}/scenes/{scene_id}")(
    resources.scene_context
)
mcp.resource("cinema://projects/{project_id}/scenes/{scene_id}")(
    resources.inherited_scene_context
)
mcp.resource("cinema://projects/{project_id}/shots/{shot_id}")(
    resources.inherited_shot_context
)
mcp.resource("cinema://runtime/{segment_id}/end-state")(
    resources.segment_end_state
)
mcp.resource("cinema://runtime/{scene_id}/audio-state")(
    resources.runtime_audio_state
)
mcp.resource("cinema://runtime/{scene_id}/editing-state")(
    resources.runtime_editing_state
)

for tool in (
    tools.compile_scene_context,
    tools.get_scene_summary,
    tools.build_scene_generation_plan,
    tools.plan_scene_production,
    tools.create_render_attempt,
    tools.validate_render_attempt,
    tools.review_render_attempt,
    tools.approve_render_attempt,
    tools.reject_render_attempt,
    tools.create_scene_release,
    tools.inspect_project_context,
    tools.compile_wan_shot,
    tools.compile_dialogue,
    tools.compile_cinematic_shot,
    tools.generate_cinematic_video,
    tools.render_wan_i2v_shot,
    tools.create_edit_plan,
    tools.validate_edit_plan,
    tools.edit_cinematic_sequence,
    tools.save_continuity_state,
    tools.finalize_cinematic_scene,
    tools.approve_wan_render,
    tools.prepare_automated_edit,
    tools.automate_scene_edit,
    tools.approve_edit_preview,
    tools.post_edit_scene,
    tools.resolve_context_chain,
    tools.validate_context_chain,
    tools.extend_cinematic_shot,
    tools.compile_segment_context,
    tools.approve_segment,
    tools.prepare_exact_dialogue,
    tools.lock_exact_dialogue,
    tools.compile_dialogue_lip_sync_context,
    tools.compile_sound_cue_sheet,
    tools.compile_music_cue_sheet,
):
    mcp.tool()(tool)


def main() -> None:
    """Execute main."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
