from __future__ import annotations

import asyncio

from little_planet_wonders.mcp.server import mcp


def test_mcp_server_registers_one_cohesive_surface() -> None:
    async def inspect() -> tuple[list[str], list[str]]:
        tools = await mcp.list_tools()
        templates = await mcp.list_resource_templates()
        return (
            [tool.name for tool in tools],
            [str(template.uri_template) for template in templates],
        )

    tool_names, resource_templates = asyncio.run(inspect())

    assert len(tool_names) == len(set(tool_names))
    assert "compile_cinematic_shot" in tool_names
    assert "validate_edit_plan" in tool_names
    assert "cinema://projects/{project_id}" in resource_templates
    assert "cinema://projects/{project_id}/audio" in resource_templates
