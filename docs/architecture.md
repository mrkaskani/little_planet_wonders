# Architecture

The generation layer owns character, location, wardrobe, camera, and prompt
consistency. The editing layer owns cuts, color matching, audio balance, rhythm,
transitions, and continuity validation. The audio layer bridges both through an
ordered shot pipeline, while the MCP layer only adapts those domain services to
resources and tools.

`context/` is treated as read-only source material. Runtime continuity created
after an edit is stored in `runtime/continuity/<project>/<scene>.yaml`.
