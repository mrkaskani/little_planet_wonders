from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from little_planet_wonders.mcp import resources, tools


mcp = MCPServer(
    "Little Planet Wonders",
    instructions=(
        "Compile cinematic generation and editing plans from project context. "
        "Use edit_cinematic_sequence before rendering edits, preserve continuity, "
        "and reject plans with blocking validation errors."
    ),
)

mcp.resource("cinema://studio")(resources.studio_context)
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
mcp.resource("cinema://projects/{project_id}/editing")(resources.editing_context)

for tool in (
    tools.inspect_project_context,
    tools.compile_wan_shot,
    tools.compile_dialogue,
    tools.compile_cinematic_shot,
    tools.generate_cinematic_video,
    tools.create_edit_plan,
    tools.validate_edit_plan,
    tools.edit_cinematic_sequence,
    tools.save_continuity_state,
):
    mcp.tool()(tool)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
