"""Compatibility entry point for the Little Planet Wonders MCP server."""

from little_planet_wonders.mcp.server import main, mcp
from little_planet_wonders.mcp.tools import (
    compile_cinematic_shot,
    compile_dialogue,
    compile_wan_shot,
    create_edit_plan,
    edit_cinematic_sequence,
    generate_cinematic_video,
    inspect_project_context,
    save_continuity_state,
    validate_edit_plan,
)

__all__ = [
    "compile_cinematic_shot",
    "compile_dialogue",
    "compile_wan_shot",
    "create_edit_plan",
    "edit_cinematic_sequence",
    "generate_cinematic_video",
    "inspect_project_context",
    "main",
    "mcp",
    "save_continuity_state",
    "validate_edit_plan",
]


if __name__ == "__main__":
    main()
