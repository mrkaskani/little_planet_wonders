"""Compatibility entry point for the Little Planet Wonders MCP server."""

from lpw.mcp.server import main, mcp
from lpw.mcp.tools import (
    build_scene_generation_plan,
    compile_scene_context,
    compile_cinematic_shot,
    compile_dialogue,
    compile_wan_shot,
    create_edit_plan,
    edit_cinematic_sequence,
    generate_cinematic_video,
    get_scene_summary,
    inspect_project_context,
    save_continuity_state,
    validate_edit_plan,
)

__all__ = [
    "build_scene_generation_plan",
    "compile_scene_context",
    "compile_cinematic_shot",
    "compile_dialogue",
    "compile_wan_shot",
    "create_edit_plan",
    "edit_cinematic_sequence",
    "generate_cinematic_video",
    "get_scene_summary",
    "inspect_project_context",
    "main",
    "mcp",
    "save_continuity_state",
    "validate_edit_plan",
]


if __name__ == "__main__":
    main()
