# ComfyUI API workflows

This directory is reserved for real, operator-tested ComfyUI API exports. LPW
supports the non-animation Wan 2.2 modes listed below.

| Mode | Required API export | Semantic bindings |
| --- | --- | --- |
| T2V | `wan22-t2v-api.json` | `wan-t2v-bindings.yaml` |
| I2V | `wan22-i2v-api.json` | `wan-i2v-bindings.yaml` |
| TI2V | `wan22-ti2v-api.json` | `wan-ti2v-bindings.yaml` |
| S2V | `wan22-s2v-api.json` | `wan-s2v-bindings.yaml` |

The binding files live in
`src/lpw/context_data/tools/workflows/`. API exports are intentionally absent
until an operator has installed the models outside this repository, built the
workflow, and verified one successful local run.

## Export requirements

Use **Export Workflow (API)** in ComfyUI. A normal UI workflow cannot be submitted
through the ComfyUI `/prompt` API and must not be saved under the names above.

Assign these semantic titles before exporting every mode:

- `MCP_POSITIVE_PROMPT`
- `MCP_NEGATIVE_PROMPT`
- `MCP_HIGH_NOISE_SAMPLER`
- `MCP_LOW_NOISE_SAMPLER`
- `MCP_VIDEO_SETTINGS`
- `MCP_OUTPUT`

Add `MCP_START_IMAGE` for I2V, TI2V, and S2V. Add `MCP_AUDIO_INPUT` for S2V.
`MCP_POSE_VIDEO` is an optional S2V conditioning input; it does not enable or
invoke Wan Animate.

The S2V export must expose semantic bindings for `steps`, `cfg`, `sampler`, and
`scheduler`, and must bind exactly one `MCP_START_IMAGE`. The active defaults are
81 frames at 16 FPS, 20 steps, CFG 6.0, UniPC, and the `simple` scheduler.
Lightning LoRA workflows use 4–5 steps and CFG 1.0. Add the verified **Wan Video
Image Resize to closest** stage before image encoding, preserving aspect ratio
and enforcing dimensions divisible by 16.

For first-frame VAE-burn mitigation, include a sacrificial duplicated reference
latent at batch index 0 and remove the decoded sacrificial image with **Image
from Batch** or equivalent. The exported clip must retain 81 usable frames and
remain aligned with the conditioning audio after removal.

If an exported node uses a different input name, update the corresponding binding
YAML. Do not hardcode ComfyUI numeric node identifiers in Python.

## Safety and artifact policy

- LPW never downloads model weights, checkpoints, encoders, or workflows.
- Wan Animate is excluded from the supported mode list.
- All Wan adapters begin disabled and have a null `weights_path`.
- Operators manage artifacts and local endpoints outside the repository.
- Enabling an adapter only permits use of an already provisioned service.

See `docs/wan22-setup.md` for the complete setup and validation contract.
