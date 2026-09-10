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

## S2V native creation versus YouTube delivery

Wan S2V creation and final delivery are separate technical stages. Do not pass
YouTube dimensions or frame counts into the native S2V workflow.

### Production and local precision profiles

Final Wan 2.2 S2V 14B production renders use BF16. Local Apple Silicon MCP and
pipeline previews use a GGUF Q4 profile and are never final render authority.
Every accepted local preview must be re-rendered and approved in BF16.

The complete local-worker contract and JSONL interface are documented in
[Wan 2.2 S2V local M4 worker](wan22-s2v-local-m4-worker.md). The local worker
requires a verified Wan S2V GGUF backend and explicitly rejects
`llama-cpp-python`, which does not implement this video diffusion architecture.

### Native Wan 2.2 S2V creation

```yaml
model: wan2.2-s2v-14b
size: "832*480"
width: 832
height: 480
frame_rate: 16
frame_count_rule: four-n-plus-one-covering-complete-audio
five_second_frames: 81
standard_sampling:
  steps: 20
  cfg: 6.0
  sampler: unipc
  scheduler: simple
```

At 16 FPS, a five-second S2V clip uses 81 frames: one initial conditioned frame
plus 80 temporal intervals. For an arbitrary locked-audio duration, round the
required interval count upward to a multiple of four and add the initial frame.
Trim any fractional tail during conforming.

The standard profile uses 20 sampling steps, CFG 6.0, UniPC, and the `simple`
scheduler. The `euler` scheduler is also allowed when a verified workflow needs
it. With an installed and approved Lightning LoRA, use 4–5 steps and CFG 1.0;
the configured default is 5 steps. Never apply Lightning settings without the
matching LoRA.

### S2V reference-image preparation

Wan S2V receives exactly one direct reference image per generated segment. Do
not bind front, side, character-sheet, and location images simultaneously. Those
assets may guide creation and review of the single coherent start image, but the
native image input receives only that final image.

Both image dimensions must be divisible by 16. Use the ComfyUI **Wan Video Image
Resize to closest** node or an equivalent verified node that preserves the
chosen aspect ratio:

| Orientation | Valid canvas | Use |
| --- | --- | --- |
| Landscape | `832x480` | Preferred project S2V canvas |
| Square | `640x640` | Square composition with moderate VRAM reduction |
| Square | `480x480` | Lower-VRAM square composition |
| Vertical | `480x832` | True vertical composition |

`832x480` is landscape, not vertical. Do not feed a landscape reference into a
square or vertical generation canvas: stretching and forced cropping are
forbidden. Leave background space around the head, hair, chin, jaw, and moving
body parts. For speaking shots, the mouth, jawline, and eyes must be readable,
unmasked, and free from crushing shadow or an extreme angle.

The reusable positive and negative image-reference prompts are stored in
`generation-records/prompts/single-start-reference--wan22-s2v--prompt-v003.yaml`.
The older timestamp sequences are storyboard review artifacts, not additional
Wan image inputs.

### First-frame VAE-burn mitigation

The ComfyUI S2V graph should add a duplicated reference latent as a sacrificial
batch item at index 0 using **Latent Cut** or an equivalent latent-batch node.
After decoding, use **Image from Batch** or an equivalent operation to discard
that sacrificial first image. Verify that the first kept frame has no saturation,
contrast, or flash artifact and that removing the frame did not shift audio/video
alignment. Qwen VL reviews at least the first eight kept frames.

### Short dialogue onset buffer

For a one-second spoken S2V asset, prepend 0.2–0.5 seconds of verified clean
silence before the first breath, phoneme, or vocalization. Generate the clean
voice first and add the exact buffer deterministically; a short fade is not a
substitute for silence. Rehash and reapprove the WAV after padding.

At 16 FPS, do not retain the unpadded 17-frame value:

- Use 21 frames when the final padded WAV is no longer than 1.25 seconds.
- Use 25 frames when it is longer than 1.25 seconds and no longer than 1.5 seconds.

The complete reusable positive and negative audio prompts are stored in
`generation-records/prompts/s2v-dialogue-audio-preparation--prompt-v001.yaml`.
They require an intact first syllable and forbid speech at time zero, onset
clicks, background noise, music, ambience, effects, reverb, and overlapping
speakers.

### YouTube landscape master

```yaml
resolution: "1920x1080"
aspect_ratio: "16:9"
frame_rate: 24
five_second_display_frames: 120
video_codec: h264
pixel_format: yuv420p
color_space: bt709
audio_codec: aac
audio_sample_rate: 48000
```

Conform `832x480` without stretching: center-crop six pixels from both the top
and bottom to obtain `832x468`, upscale to `1920x1080`, and convert 16 fps to
24 fps. Qwen VL must review interpolation and upscale results for face, mouth,
eye, paw, feather, fur, contact, and background-geometry artifacts. The native
480p output is never a direct YouTube master.

## No-generation verification

Safe setup verification consists of configuration compilation, workflow-path
checks, semantic binding tests, dry-run scene planning, and package compilation.
It does not queue prompts, download outputs, or generate animation/video.
