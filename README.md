# LPW

LPW compiles cinematic project context into Wan 2.2
shot packages, dialogue plans, complete audio/video production plans, and validated
editing timelines. Structured project context lives in `src/lpw/context_data/`;
generated continuity state is written separately to `runtime/`.

## Setup

```bash
uv sync --dev
uv run pytest
uv run lpw
```

Complete documentation starts at [docs/index.md](docs/index.md). The documentation
includes setup, configuration, context, Wan 2.2, audio, validation, editing,
runtime storage, MCP, testing, and generated Python API references.

Optional environment variables:

- `CINEMATIC_CONTEXT_ROOT`: legacy cinematic context directory
- `CINEMATIC_WORKFLOWS_ROOT`: ComfyUI workflows (defaults to `./workflows`)
- `CINEMATIC_RUNTIME_ROOT`: generated state (defaults to `./runtime`)

## Structure

```text
src/
└── lpw/
    ├── audio/         dialogue defaults, compilation, and shot pipeline
    ├── context/       context loaders, compilers, and existing project context
    ├── context_data/  project, story, production, tool, and workflow YAML
    ├── editing/       edit planning, continuity validation, and runtime state
    ├── generation/    Wan packages, workflow jobs, and production execution
    ├── mcp/           MCP resources, tools, and the single server entry point
    ├── validation/    render storage, media checks, reviews, and approvals
    └── utils/         YAML/JSON I/O, hashing, IDs, merging, and references
```

The root-level Python modules remain as small compatibility imports for callers
that used the original module names.

## Audio MCP surface

- `cinema://projects/{project_id}/audio` returns the resolved audio context.
- `cinema://projects/{project_id}/voices/{character_id}` returns a voice profile.
- `compile_dialogue` compiles voice, performance, pronunciation, and technical rules.
- `compile_cinematic_shot` combines the Wan video package with dialogue, music,
  ambience, sound effects, mixing, and a context hash.

## Story context

`SceneContextPipeline` compiles the sample hierarchy under
`src/lpw/context_data/`. It validates project, story, scene, and shot
relationships, resolves scene props and character wardrobe, and validates
per-shot continuity before returning a complete scene or ordered generation
plan.

The same operations are exposed through `compile_scene_context`,
`get_scene_summary`, `build_scene_generation_plan`, and the
`cinema://stories/{story_id}/scenes/{scene_id}` resource.

## Scene production

External voice, image, Wan/ComfyUI, audio, and editing providers are configured
under `src/lpw/context_data/tools/`; scene-level orchestration is configured under
`src/lpw/context_data/production/`. The MCP tool `plan_scene_production` compiles
these settings into a safe dry-run plan without contacting any external service.

The recommended Molmo2/Qwen analysis and editing roles are declared in
`editing-models.yaml`. Its `download_policy` is `never`: model artifacts must be
installed and served externally, and every model-backed adapter starts disabled.

Actual execution is owned by `SceneGenerationPipeline` in the generation package.
It only runs with `dry_run=False`, validates that every required provider is
enabled, then generates missing inputs, submits the selected Wan workflows,
normalizes and concatenates clips, and mixes the scene audio with FFmpeg.

## Render validation and approval

Rules under `src/lpw/context_data/validation/` are compiled with the complete
scene context. `RenderValidationPipeline` stores each generated shot in a new
`attempt-NNNN` directory under `renders/`, snapshots its context, hashes the
media and manifests, runs FFprobe/FFmpeg checks, and records semantic reviews and
one immutable approval or rejection decision. A scene release requires a current,
approved attempt for every shot and is stored as a new `release-NNNN` directory.

The MCP surface exposes `create_render_attempt`, `validate_render_attempt`,
`review_render_attempt`, `approve_render_attempt`, `reject_render_attempt`, and
`create_scene_release`. All paths are constrained to render storage; context YAML
remains read-only.

## ComfyUI and Wan 2.2 integration

LPW configures Wan 2.2 T2V, I2V, TI2V, and S2V. Wan Animate is deliberately
excluded. Every adapter starts disabled, has no repository-managed weight path,
and uses a `download_policy` of `never`. Operators provide already-installed
model artifacts, a local ComfyUI endpoint, and real API-format workflow exports.

The `render_wan_i2v_shot` MCP tool is the implemented execution path. It compiles
an existing `ShotRequest`, loads the real I2V API workflow, applies semantic
bindings by `_meta.title`, uploads the approved start frame, submits the graph,
polls ComfyUI history, and stores all provenance beside the downloaded result.
The other modes are fully declared for safe operator integration but remain
disabled until their provider execution paths are connected and verified.

Export tested graphs under `workflows/comfyui/` using the filenames documented in
that directory's README. Semantic bindings live under
`src/lpw/context_data/tools/workflows/`, while the HTTP client lives under
`lpw.integrations` and render orchestration remains under `lpw.generation`. The
resolved policy is available from `cinema://studio/wan22`.

The editing stack declares disabled local-service roles for Molmo2 visual
analysis, Qwen3-Omni audiovisual analysis, Qwen3 planning, and the optional
Molmo2-4B/Qwen3-4B/Whisper/CLAP lightweight profile. Planner services must return
the strict contract in `tools/schemas/edit-decision-list.schema.json`. The
project never installs or downloads model artifacts; operators provide endpoints
for already-managed local services.

## Context chaining and shot extension

Version-pinned `cinema://` inheritance is resolved by `lpw.context.chaining`.
The resolver detects circular inheritance, rejects `@latest`, applies explicit
imports, overrides, and patches, and prevents child contexts from changing
immutable fields. The classroom rooftop example includes studio, project,
sequence, scene, shot, and three four-second segment contexts.

`extend_cinematic_shot` creates a versioned plan under `runtime/extensions/` and
compiles only the first segment. `approve_segment` accepts real provider artifacts
and a stable reviewed end frame, records analysis and an event-sourced continuity
delta, and creates an editorial event. Only then can `compile_segment_context`
copy that approved frame into the next segment and apply the cumulative runtime
state. Model generation and analysis remain external, disabled services; these
tools never download weights and never fabricate successful generation.

## Voice, sound-effects, and music production

Audio production is split into three independent services. `prepare_exact_dialogue`
selects permanent voice identity and emotional-reference guidance while preserving
the exact approved words. `lock_exact_dialogue` accepts only an existing clean WAV,
an exact verified transcript, and passing identity, accuracy, emotional-safety,
and listening-comfort reviews. `compile_dialogue_lip_sync_context` then exposes the
locked file and checksum as the authoritative lip-sync input.

`compile_sound_cue_sheet` validates visible sources, materials, timing, distance,
layer limits, and forbidden child-unsafe qualities. `compile_music_cue_sheet`
preserves reusable themes, ducks and simplifies under speech, and reserves three
to five seconds of quiet musical space for audience participation. Missing assets
remain `not-run` external-provider tasks; the project creates no placeholder audio
and downloads no voices, effects, music, or model files.

## Classroom finalization

The final-pipeline recommendation is represented by the existing `classroom`
project. Its project-specific delivery rules are in
`src/lpw/context/projects/classroom/export.yaml`, and its rooftop timeline is in
`src/lpw/context/projects/classroom/scenes/rooftop-confrontation/timeline.yaml`.

`approve_wan_render` records immutable scored creative approval beside a completed
package-hash render. `finalize_cinematic_scene` then validates every timeline
source and approval, normalizes compatible clips, assembles hard cuts, ducks music
under dialogue, mixes the four audio stems, validates the final output, and writes
the versioned export. Authoritative continuity is committed under `runtime/` only
after that export succeeds; source context remains unchanged.

## Automated editing workflow

Classroom automation policies are separated into `editing_style.yaml`,
`auto-editing.yaml`, `post-editing.yaml`, `take-selection.yaml`, `color-grade.yaml`,
`subtitles.yaml`, and the scene-specific `edit-context.yaml`. These files remain
read-only production context.

The controlled MCP workflow is:

1. `prepare_automated_edit` validates approved media, hashes metadata, records
   technical reports, scores available takes, and writes a versioned prepared
   package under `edits/`.
2. `automate_scene_edit` selects valid takes, builds a video/audio EDL, checks
   adjacency, renders a review proxy, and enters `awaiting-review`.
3. `approve_edit_preview` records the immutable edit decision.
4. `post_edit_scene` converts structured review notes into a versioned patch. An
   unchanged approved edit proceeds through finalization and produces a checksum
   archive manifest under `archive/`.

Disabled visual-analysis, cleanup, grading, subtitle, and master-profile providers
are reported as `not-run`; the pipeline never claims those operations completed.
