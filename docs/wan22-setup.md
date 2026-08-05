# Wan 2.2 setup

LPW configures four Wan 2.2 modes and deliberately excludes Wan Animate.
The mode names follow the
[official Wan2.2 model catalog](https://github.com/Wan-Video/Wan2.2#model-download).

| Mode | Model declaration | Purpose | Workflow ID |
| --- | --- | --- | --- |
| T2V | `wan2.2-t2v-a14b` | final text-to-video shots | `wan-t2v` |
| I2V | `wan2.2-i2v-a14b` | reference/start-frame shots | `wan-i2v` |
| TI2V | `wan2.2-ti2v-5b` | efficient drafts with optional image | `wan-ti2v` |
| S2V | `wan2.2-s2v-14b` | locked-dialogue sound-to-video | `wan-s2v` |

## Hard exclusions

```yaml
download_policy: never
artifact_policy: externally-managed
animation:
  enabled: false
```

The compiler rejects a manifest that enables animation, declares weight paths,
enables a model by default, or omits one of the four supported modes.

## ComfyUI workflow setup

LPW does not ship fabricated or UI-format workflow JSON. For each mode:

1. Install ComfyUI and the required nodes outside this repository.
2. Make already-managed model artifacts available to that installation.
3. Build and verify the workflow manually in ComfyUI.
4. Assign the semantic node titles listed in `workflows/comfyui/README.md`.
5. Export with **Export Workflow (API)**.
6. Save to `workflows/comfyui/wan22-<mode>-api.json`.
7. Keep `wan22-comfyui.enabled: false` while validating the graph.
8. Enable execution only in a controlled local configuration.

Expected files are intentionally absent until supplied by an operator:

```text
workflows/comfyui/wan22-t2v-api.json
workflows/comfyui/wan22-i2v-api.json
workflows/comfyui/wan22-ti2v-api.json
workflows/comfyui/wan22-s2v-api.json
```

Semantic binding files are source controlled under
`src/lpw/context_data/tools/workflows/`. Update bindings when node titles or input
names change; do not hardcode exported numeric IDs into domain services.

## Mode selection

- `draft` selects TI2V 5B.
- `text_to_video` selects T2V A14B.
- `image_to_video` selects I2V A14B and requires an approved reference.
- `dialogue` selects S2V 14B and requires locked clean dialogue plus a reference.
- `performance`/Wan Animate is rejected.

## No-generation verification

Safe setup verification consists of configuration compilation, workflow-path
checks, semantic binding tests, dry-run scene planning, and package compilation.
It does not queue prompts, download outputs, or generate animation/video.
