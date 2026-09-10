# Production video generation and restoration

The project now has one quality-gated route from approved inputs to the 1080p
master. Its policy authority is
`src/lpw/context/projects/riri-yoyo/production-restoration.yaml`. The MCP
resource `cinema://projects/{project_id}/production-restoration` exposes the
complete policy, and `plan_production_restoration` creates a deterministic plan
without loading or running heavyweight models.

## Ordered production path

1. Qwen3-VL checks script, prompts, reference identity and geometry, audio, image
   defects, talking-head margins, dimensions, and aspect ratio. A failed input
   check stops before generation.
2. Wan 2.2 S2V A14B creates the native 832×480, 16 fps candidate. A five-second
   segment uses exactly 81 frames. Production precision is BF16; the local
   GGUF Q4_K_S route remains a preview and integration-test profile.
3. Qwen3-VL reports structured generated-video defects with exact bad-frame
   bounds, evidence, severity, confidence, violated authority, and one bounded
   repair action.
4. Only the matching repair runs: CodeFormer for a bounded face defect,
   LatentSync 1.6 for a speaking lip-sync defect with locked dialogue, or a
   padded Wan segment reprocess for temporal and other visual defects.
5. Practical-RIFE performs 2× temporal interpolation.
6. SeedVR2 performs video-aware restoration in overlapping temporal chunks and
   writes an explicit 1920×1080 result. The default 32-frame chunks overlap by
   eight frames; completed chunks can be offloaded to CPU memory.
7. FFmpeg creates a ProRes master and YouTube MP4 delivery, validates timestamps,
   audio synchronization, pixel format, color metadata, and output dimensions.
8. Qwen3-VL compares approved references, the pre-restoration candidate, and the
   final output. Human review is still required for final promotion.

The default order is RIFE then SeedVR2. A difficult segment may generate the
opposite order as a second immutable candidate, but one difficult segment does
not change the order for the entire project.

## SeedVR2 selection and memory policy

Model selection is explicit and quality ordered: 7B FP16, 7B high-quality
reduced precision, 7B quantized, then 3B only as a last resort. Every selection
below 7B FP16 creates a downgrade record containing the hardware profile,
reason, and expected compromise. There is no silent fallback.

Only one heavyweight model should be device-resident at a time. Each stage
writes its manifest before unloading the model and clearing device caches.
Restoration uses overlapping temporal chunks rather than isolated frames to
avoid shimmer and identity changes.

## Evidence, retries, and completion

Source frames and intermediate candidates are lossless and immutable. Rejected
candidates remain available with their source hash, model, precision,
parameters, frame ranges, output hash, and QA decision. Repairs make a new
candidate and affect only the defective interval plus stable boundary padding.

A video is not complete because it is sharper. Completion requires all visual
QA categories to pass, no unresolved severe defects, valid master and delivery
files, audio synchronization and loudness checks, a complete immutable manifest,
and recorded human promotion. Failed categories trigger a selective padded
retry instead of a full-video retry.

## Current executor status

The repository now contains the production policy and MCP planning layer.
Qwen3-VL, CodeFormer, LatentSync 1.6, Practical-RIFE, and SeedVR2 executors and
weights are deliberately marked disabled until their external runtime paths are
configured and verified. The planning tool returns each disabled dependency in
`blocking_requirements`; it never labels such a plan executable. FFmpeg is the
only enabled post-production executor in this policy.

Example planning request:

```json
{
  "project_id": "riri-yoyo",
  "source_frames": "/absolute/path/to/immutable/native-frames",
  "hardware_profile": "local-limited",
  "has_dialogue": true,
  "defects": ["face", "lip_sync"],
  "difficult_scene": true,
  "available_vram_gb": 12.5
}
```

Allowed defect values are `face`, `lip_sync`, and `temporal`. Requesting
`lip_sync` without locked dialogue is rejected because LatentSync must not infer
or replace the approved spoken performance.
