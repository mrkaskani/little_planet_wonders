# Little Planet Wonders

Little Planet Wonders compiles read-only cinematic project context into Wan 2.2
shot packages, dialogue plans, complete audio/video pipeline plans, and validated
editing timelines. Generated continuity state is written to `runtime/`, never to
`context/`.

## Setup

```bash
uv sync --dev
uv run pytest
uv run little-planet-wonders
```

Optional environment variables:

- `CINEMATIC_CONTEXT_ROOT`: context source directory (defaults to `./context`)
- `CINEMATIC_WORKFLOWS_ROOT`: ComfyUI workflows (defaults to `./workflows`)
- `CINEMATIC_RUNTIME_ROOT`: generated state (defaults to `./runtime`)

## Structure

```text
little_planet_wonders/
├── audio/       dialogue defaults, compilation, and shot pipeline
├── context/     normalized loading of flat and nested context schemas
├── editing/     edit planning, continuity validation, and runtime state
├── generation/  Wan models, prompts, packages, and workflow jobs
├── mcp/         MCP resources, tools, and the single server entry point
└── utils/       YAML/JSON I/O, hashing, IDs, merging, and references
```

The root-level Python modules remain as small compatibility imports for callers
that used the original module names.
