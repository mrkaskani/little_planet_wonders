# Local validation and production execution environments

The pipeline has two isolated configurations under `config/pipeline/`:

- `local.yaml` minimizes computational cost and can never authorize production.
- `production.yaml` selects BF16 Wan 2.2 S2V, SeedVR2 7B, maximum-quality audio,
  1080p restoration, and a separate production artifact tree.
- `models.yaml` is the centralized model registry.
- `hardware.yaml` declares environment-specific RAM, disk, and accelerator gates.

Local and production data, logs, caches, jobs, outputs, and reports are stored in
different `runtime/pipeline/local/` and `runtime/pipeline/production/` trees.
Production configuration cannot consume a local Q4 Wan result as final authority.

## Commands

```bash
.venv/bin/python -m lpw.pipeline_cli check --environment local
.venv/bin/python -m lpw.pipeline_cli test
.venv/bin/python -m lpw.pipeline_cli production
```

`check` writes hardware, dependency, model, MCP, and consolidated check reports.
It never downloads or loads heavyweight model weights. `test` creates the
component-test and local-readiness reports. Components without current smoke-test
evidence remain `NOT_RUN`; this is a failure, not an implicit pass.

`production` currently performs preflight only. It verifies that the exact local
readiness report says `production_ready: true`, then validates production
hardware, disk, dependencies, models, and MCP. Any failure returns a structured
blocker and `generation_started: false`.

## Production weight downloads

Resumable wget-only production download scripts are documented in
[Production weight downloads](../scripts/models/README-production-downloads.md).
The aggregate script requires at least 230 GiB free and refuses before transfer
when that threshold is not met. Every Hugging Face model is pinned to an exact
commit and each completed file must match the repository metadata byte count.

Equivalent MCP operations are:

- `pipeline_system_status`
- `validate_local_pipeline`
- `run_production_preflight`

The model registry and environment configurations are available as
`cinema://pipeline/models` and
`cinema://pipeline/environments/{environment}`.

## Current host limitation

The Apple M4 machine is a local integration host. Its working MPS backend and
Wan Q4_K_S model can validate local tensor and generation wiring, but the
production configuration requires a CUDA production host and BF16 Wan weights.
No precision or model downgrade is automatic.
