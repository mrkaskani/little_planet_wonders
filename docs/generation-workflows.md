# Generation workflows

## Shot package compilation

`compile_wan_shot` performs these local steps:

1. Validate identifiers, shot type, duration, and mode-specific inputs.
2. Load project, character, location, camera, visual, and continuity context.
3. Build positive and negative prompts.
4. Select T2V, I2V, TI2V, or S2V.
5. Select primary and supporting references.
6. Calculate Wan-compatible `4n+1` frame count.
7. Generate or preserve a deterministic seed.
8. Return a typed package with context and package hashes.

Compilation does not load a model or invoke ComfyUI.

## Scene production planning

`plan_scene_production` calls `SceneGenerationPipeline.produce_scene(...,
dry_run=True)`. It resolves each shot, required audio assets, provider roles,
workflow bindings, and output plan without calling any external provider.

Real production requires `dry_run=False` in domain code and all referenced tools
to be explicitly enabled. Disabled tools produce a clear error.

## I2V render boundary

`render_wan_i2v_shot` is the controlled ComfyUI path:

1. Compile the shot package.
2. Require a real API-format workflow.
3. Apply semantic bindings.
4. Upload the approved input frame.
5. Queue the workflow and poll history.
6. Download the actual provider output.
7. Store package, graph, history, result, and output together.

The tool never downloads model weights. It should remain unused until the local
provider and workflow are deliberately enabled.

## S2V two-phase boundary

Phase 1 creates local dialogue turns, music, ambience, Foley, and effects. The
project owner creates the coherent scene-reference image manually and supplies
it through the documented handoff. Every selected asset receives a path,
SHA-256, context hash, provenance record, and human approval.

Phase 2 compiles each speaking unit from exactly one approved image and one
speaker's locked clean dialogue WAV. Music, ambience, Foley, effects, and a
combined multi-speaker conversation are excluded from S2V conditioning. They
remain separate stems and are added after picture generation. Later speaking
segments inherit the previous approved end frame unless a deliberate cut has a
separately approved start frame.

The detailed contracts are documented in the Creating Scenes course:
[Phase 1](courses/creating_scenes/phase_01_create_audio_and_scene_reference.md)
and [Phase 2](courses/creating_scenes/phase_02_generate_s2v_and_final_mix.md).

## Chained shot extension

`extend_cinematic_shot` divides a target duration into short segments and writes a
versioned plan. Only segment one becomes ready initially.

For every subsequent segment:

1. A real provider creates video.
2. Analysis identifies blocking defects and stable frames.
3. A reviewer approves a stable end frame.
4. `approve_segment` stores the video, frame, analysis, delta, and editorial event.
5. `compile_segment_context` copies that frame as the next start frame.
6. Cumulative runtime continuity is applied.

Future segments remain blocked until the predecessor is approved.
