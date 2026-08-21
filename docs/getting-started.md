# Getting started

## Requirements

- Python 3.11 or newer
- `pip`
- FFmpeg and FFprobe for media validation and finalization
- Optional local ComfyUI only when an operator chooses to execute Wan workflows

Model weights, checkpoints, LoRAs, and VAEs are deliberately not project
dependencies. Install and manage them outside this repository if generation is
later enabled.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

If the repository already contains its virtual environment and network access is
intentionally unavailable, use the existing environment:

```bash
.venv/bin/pytest -q
```

## Verify

```bash
pytest
python -m compileall -q src tests
```

## Start the MCP server

```bash
lpw
```

The server uses stdio transport. Configure the command and project directory in
the MCP host rather than launching it as an HTTP server.

## First safe operations

1. Read `cinema://studio/wan22` to inspect disabled Wan declarations.
2. Read `cinema://projects/riri-yoyo` to inspect the approved project foundation.
3. Call `plan_scene_production` to create a dry-run plan.
4. Call `compile_wan_shot` to inspect a package without rendering.
5. Keep `wan22-comfyui.enabled` set to `false` until local assets and API workflows
   have been verified by an operator.

## What setup does not do

Setup does not:

- download any model or media file;
- install ComfyUI;
- fetch custom nodes;
- create placeholder workflow graphs;
- invoke video generation or animation;
- approve output automatically.
