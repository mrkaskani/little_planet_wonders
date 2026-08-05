# ComfyUI API workflows

Place the real ComfyUI API export for Wan 2.2 I2V at:

```text
workflows/comfyui/wan22-i2v-api.json
```

Do not place a normal UI workflow here. In ComfyUI, use **Export Workflow
(API)** after the workflow runs successfully.

Assign these titles to the corresponding nodes before exporting:

- `MCP_POSITIVE_PROMPT`
- `MCP_NEGATIVE_PROMPT`
- `MCP_START_IMAGE`
- `MCP_HIGH_NOISE_SAMPLER`
- `MCP_LOW_NOISE_SAMPLER`
- `MCP_VIDEO_SETTINGS`
- `MCP_OUTPUT`

The semantic mapping is maintained separately in
`src/lpw/context_data/tools/workflows/wan-i2v-bindings.yaml`. If the exported
nodes use different input names, update that YAML rather than hardcoding numeric
node IDs in Python.

Model files and checkpoints are externally managed and must not be downloaded
into this repository.
