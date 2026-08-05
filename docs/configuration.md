# Configuration

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `CINEMATIC_CONTEXT_ROOT` | `src/lpw/context` | Legacy/nested project context root |
| `CINEMA_CONTEXT_ROOT` | unset | Backward-compatible context-root alias |
| `CINEMATIC_WORKFLOWS_ROOT` | `workflows/` | Operator-supplied ComfyUI API exports |
| `CINEMATIC_RENDER_ROOT` | `renders/` | Versioned render attempts and releases |
| `CINEMATIC_RUNTIME_ROOT` | `runtime/` | Generated continuity and production state |

## Context roots

LPW currently supports two complementary context layouts:

- `src/lpw/context_data/` contains the normalized story/scene/shot compiler data.
- `src/lpw/context/` contains nested studio and project context used by cinematic
  resources, audio compilation, editing, and inheritance.

Generated state belongs under `runtime/`, `renders/`, `edits/`, or `archive/`.
Never store generated approvals or provider outputs inside either context root.

## Provider configuration

External tools are declared in
`src/lpw/context_data/tools/generation-tools.yaml`. Each tool specifies:

- `kind` and `provider`;
- `enabled`, which is `false` for model-backed providers;
- transport (`http-json`, `comfyui`, or `subprocess`);
- endpoint and timeout settings;
- output-field or executable settings.

`ffmpeg` is the only enabled executor by default. Enabling another provider is an
operator decision and should happen only after its local service, files, and
licenses are verified.

## Model policy

`editing-models.yaml` and `wan22-models.yaml` use:

```yaml
download_policy: never
artifact_policy: externally-managed
```

Wan declarations additionally require `weights_path: null` in source context.
Runtime service configuration may point to an externally managed installation,
but no downloader is implemented by this project.

## Output directories

The following paths are ignored by Git:

- `runtime/`
- `renders/`
- `edits/`
- `archive/`
- build, cache, coverage, and IDE directories

This separation prevents generated state from silently changing source context.
