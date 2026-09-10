# Wan 2.2 S2V local M4 worker

## Direct GGUF/MPS feasibility probe

The non-ComfyUI backend now includes a bounded direct-loader probe. It checks
the downloaded GGUF tensor names and shapes against Alibaba's official
`WanModel_S2V` 14B architecture, streams one Q4_K/Q5_K transformer block
through CPU dequantization into MPS BF16, runs representative attention and
FFN kernels, and records process plus MPS unified-memory measurements.

Install the experimental dependencies and run it with:

```bash
.venv/bin/python -m pip install -e '.[s2v-mps]'
scripts/video/probe_wan22_s2v_gguf_mps.sh
```

The machine-readable block report is written to
`runtime/diagnostics/wan22-s2v-gguf-mps-block-0.json`. Passing this probe proves
one-block loading and MPS kernel compatibility. The complete direct execution
graph now builds on this verified loader.

Measured on the 16 GB Apple M4 Mac mini:

- all 1,260 GGUF tensors matched the S2V component layout;
- all 40 main transformer blocks contain the official 27 tensors;
- block 0 retained 702,788,608 bytes in MPS BF16;
- extrapolating the identical main-block layouts gives 28,111,544,320 bytes
  for 40 resident BF16 blocks, beyond both physical memory and the MPS
  recommended allocation limit;
- the process RSS increase has been roughly 0.67-0.73 GB at block-load time,
  varying between runs as the operating system faults memory-mapped pages;
- MPS driver allocation peaked at 1,082,621,952 bytes in this probe;
- one-token BF16 attention and FFN kernels completed with finite outputs;
- tracked MPS allocation returned to zero after block release.

The GGUF is a mixed quantization artifact despite its Q4_K_S profile name:
356 tensors are Q4_K, 44 are Q5_K, 67 are BF16, and 793 small or sensitive
tensors are F32. A direct runtime must therefore dispatch by each tensor's GGUF
type rather than assuming every tensor uses four-bit storage.

Consequently the direct backend must memory-map the GGUF and stream one block
at a time. Materializing the whole transformer as ordinary PyTorch BF16
parameters is explicitly unsupported on this 16 GB target. True in-place Q4_K
Metal kernels could improve speed later, but this probe uses the safer first
implementation: CPU dequantization followed by a bounded MPS BF16 block.

The LPW local worker is a persistent JSONL process for sequential Wan 2.2 S2V
preview jobs on a base M4 Mac with 16 GB unified memory. It separates two model
authorities:

| Profile | Model format | Purpose | Final authority? |
| --- | --- | --- | --- |
| Production | BF16 | Final candidate rendering | Yes |
| Local M4 | GGUF Q4 | MCP, orchestration, timing, framing, and broad-motion previews | No |

Every local preview selected for delivery must be re-rendered and approved using
the production BF16 profile.

## Backend boundary

The worker does not use `llama-cpp-python`. GGUF is a container format, not a
guarantee that a runtime implements the model architecture. `llama.cpp` does not
provide a Wan 2.2 S2V video diffusion executor. The official Wan implementation
uses its own PyTorch S2V pipeline. LightX2V does not document a Wan S2V GGUF
backend for Apple MPS, and Diffusers does not document a complete S2V pipeline
using this GGUF checkpoint and GGUF UMT5 encoder.

The project now provides the verified backend module
`lpw.generation.wan_s2v_backend`. It fails at startup when its dependencies or
required tensors are absent and still rejects `llama_cpp`. No placeholder video
is produced.

The backend module must export:

```python
def create_backend(config: dict, emit, cleanup):
    """Load the S2V model, encoders, and VAE exactly once and return a backend."""
```

The returned object must implement:

```python
def generate_to_directory(self, job: dict, frame_directory: str, emit) -> int:
    """Write 00000.png through 00080.png sequentially and return 81."""
```

The backend uses CPU memory-mapped GGUF storage and bounded MPS BF16 execution.
It synchronizes and clears MPS allocations between streamed layers and phases.
No LoRA is loaded because there is no verified S2V-specific four-step LoRA in
the selected local package.

## Implemented direct pipeline

The direct backend includes:

- selected-row Q6_K token embedding and 24 streamed UMT5-XXL encoder layers;
- the strict 424-tensor FP16 Wav2Vec2 XLSR-53 speech encoder;
- the S2V causal audio projection and all 12 trained audio injection layers;
- reference, condition-mask, temporal, and text projection layers;
- FramePack projection and negative-time rotary positions;
- all 40 Q4_K/Q5_K S2V blocks with MPS BF16 SDPA;
- CPU float64 timestep embeddings where MPS has no float64 support;
- flow-prediction UniPC with 20 steps, shift 3.0, and CFG 6.0;
- strict conversion of the Wan 2.1 BF16 VAE into `AutoencoderKLWan`;
- 128×128 tiled VAE decoding with immediate CPU offload of temporal results;
- atomic UniPC scheduler checkpoints after every completed diffusion step;
- a durable final-latent checkpoint before VAE decoding and decode-only retry;
- deterministic seeded noise and sequential `00000.png` to `00080.png` output.

An end-to-end one-step diagnostic passed with real episode prompt/audio and
wrote 81 frames. It used a 16×16 canvas to validate the entire graph and took
194.279 seconds. This is not a quality or production-speed benchmark. A full
832×480, 20-step CFG render performs 40 denoiser evaluations (conditional and
unconditional for every step), each containing 40 streamed blocks, and can take
several hours on the base 16 GB M4.

Run the configured 832×480 persistent worker with:

```bash
scripts/video/run_wan22_s2v_local_worker.sh
```

Repeat the bounded end-to-end diagnostic with:

```bash
.venv/bin/python scripts/video/smoke_wan22_s2v_direct_backend.py \
  --model-root models/wan22-s2v-local-q4ks \
  --reference /absolute/reference.png \
  --audio /absolute/five-second-audio.wav \
  --output runtime/diagnostics/wan22-s2v-direct-e2e-smoke
```

Use `--width 832 --height 480 --steps 1` for a full-canvas setup validation.
The smoke command writes scheduler state under a sibling `checkpoints` directory.
To retry only a failed VAE decode, pass the saved checkpoint back without
repeating diffusion:

```bash
.venv/bin/python scripts/video/smoke_wan22_s2v_direct_backend.py \
  --model-root models/wan22-s2v-local-q4ks \
  --reference /absolute/reference.png \
  --audio /absolute/five-second-audio.wav \
  --output runtime/diagnostics/wan22-s2v-decode-retry/frames \
  --width 832 --height 480 --steps 1 \
  --decode-checkpoint /absolute/checkpoints/final-latents.safetensors
```

The persistent worker stores checkpoints under
`<output-root>/checkpoints/<job-id>/`. Submitting the identical job again restores
the UniPC latent, model-output history, timestep history, corrector sample, and
step index. A changed prompt, negative prompt, reference, audio, seed, canvas,
frame rate, step count, or CFG produces a different signature and starts cleanly.

## Fixed local parameters

```yaml
device: mps
format: gguf
quantization: q4-k-s
frames: 81
fps: 16
steps: 20
cfg: 6.0
default_dimensions: 480x480
text_encoder: {device: cpu, format: gguf, quantization: q4-k-s}
audio_encoder: {device: cpu, dtype: float16}
lora: {enabled: false}
```

The default 480×480 canvas is divisible by 16 and reduces local memory pressure.
The worker also accepts other dimensions of at least 384×384 when both dimensions
are divisible by 16 and the reference image matches exactly.

The worker sets `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` before any backend can
import PyTorch, as required by the local profile. Zero disables the normal MPS
allocation ceiling; it is not intrinsically a safe memory limit. The worker
therefore permits only one job at a time and performs synchronous cache cleanup.

## Required environment variables

```bash
export LPW_WAN_S2V_BACKEND_MODULE='lpw.generation.wan_s2v_backend'
export LPW_WAN_S2V_GGUF='/absolute/models/Wan2.2-S2V-14B-Q4_K_S.gguf'
export LPW_WAN_S2V_VAE='/absolute/models/wan_2.1_vae.safetensors'
export LPW_WAN_S2V_TEXT_ENCODER='/absolute/models/umt5-xxl-encoder-Q4_K_S.gguf'
export LPW_WAN_S2V_TOKENIZER='/absolute/models/umt5-tokenizer'
export LPW_WAN_S2V_AUDIO_ENCODER='/absolute/models/wav2vec2_large_english_fp16.safetensors'
```

LPW never downloads these artifacts. Confirm that every path belongs to the
verified backend and exact S2V model family.

## Validate without loading models

```bash
lpw-wan-s2v-local --validate-only
```

Validation checks the GGUF magic header, all required files, ffmpeg, dimensions,
fixed 81/16/20/6.0 parameters, and the forbidden-backend list. Use the block and
end-to-end probes above for numerical execution checks.

## Persistent MCP loop

Start the worker once:

```bash
lpw-wan-s2v-local \
  --output-root runtime/video/local-s2v \
  --width 480 \
  --height 480
```

Write one JSON object per line to stdin. Stdout contains JSON objects only.

Health request:

```json
{"command":"health"}
```

Generation request:

```json
{"command":"generate","job_id":"episode-001-segment-001","prompt":"Riri speaks softly while Yoyo listens.","negative_prompt":"identity drift, cropped face, extra limbs","reference_image":"/absolute/reference.png","audio_path":"/absolute/dialogue-padded.wav","output_path":"episode-001-segment-001.mp4","seed":42}
```

Shutdown request:

```json
{"command":"shutdown"}
```

The reference must be a PNG matching the configured dimensions. The audio must
be uncompressed mono PCM WAV with 0.2–0.5 seconds of exact digital silence before
the first nonzero sample. Output paths are confined to the configured output
root.

## Frame and media handling

The backend writes one compressed PNG at a time. The worker verifies exactly 81
files named `00000.png` through `00080.png`, checks every frame dimension, and
then invokes ffmpeg with H.264/YUV420p and AAC 48 kHz audio. Temporary frames are
removed only after a successful MP4 is atomically moved to its final path.

## Production promotion gate

A local Q4 preview may approve orchestration and broad creative direction, but
not fine facial quality, fur/feather detail, or final identity fidelity. Before
delivery:

1. Re-run the accepted job with the BF16 production profile.
2. Apply the same reference, audio hash, prompt, seed, timing, and camera state.
3. Run Qwen VL continuity and artifact review.
4. Require final human approval.

## Primary implementation references

- [Official Wan 2.2 repository](https://github.com/Wan-Video/Wan2.2)
- [Official Wan S2V generation entry point](https://github.com/Wan-Video/Wan2.2/blob/main/generate.py)
- [LightX2V repository](https://github.com/ModelTC/LightX2V)
- [LightX2V model structure and dual-noise configuration](https://github.com/ModelTC/LightX2V/blob/main/docs/EN/source/getting_started/model_structure.md)
