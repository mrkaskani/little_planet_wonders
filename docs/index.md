# LPW documentation

LPW is a context-driven cinematic planning and production-control MCP server. It
compiles immutable YAML context into reproducible generation, audio, validation,
editing, and delivery packages. External generators are optional, disabled by
default, and never allowed to download model weights through this repository.

## Documentation map

- [Getting started](getting-started.md): local setup, commands, and first checks.
- [Architecture](architecture.md): package ownership and end-to-end data flow.
- [Configuration](configuration.md): environment variables and provider policies.
- [Context system](context-system.md): schemas, compilation, inheritance, and hashes.
- [Creating a project context](creating-project-context.md): step-by-step project,
  character, voice, location, audio, scene, shot, continuity, and editing setup.
- [Wan 2.2 setup](wan22-setup.md): T2V, I2V, TI2V, and S2V configuration.
- [Stable Audio 3 Medium on Apple Silicon](stable-audio-3-medium-mlx.md):
  local MLX setup, safe wrappers, SFX generation, and verification.
- [Generation workflows](generation-workflows.md): scene and shot planning flows.
- [Audio workflows](audio-workflows.md): voice, lip sync, ambience, effects, and music.
- [Character voice profiles](voice-profile.md): per-reference text, prompts, and identity locking.
- [Cloned character conversations](cloned-conversations.md): JSON dialogue generation using profile-locked voices.
- [Validation and approval](validation-and-approval.md): attempts, reviews, and releases.
- [Editing workflows](editing-workflows.md): preparation, EDLs, previews, and delivery.
- [Runtime storage](runtime-storage.md): artifact layout and immutability boundaries.
- [MCP reference](mcp-reference.md): every resource and high-level tool group.
- [Testing](testing.md): test commands and safety assertions.
- [Python API reference](api-reference.md): generated module/class/function signatures.

## Safety boundaries

The following guarantees apply to every workflow:

1. Source context is not rewritten by runtime operations.
2. Model weights are externally managed and never downloaded by LPW.
3. Wan Animate is not configured or selectable.
4. T2V, I2V, TI2V, and S2V providers start disabled.
5. Dry-run planning does not contact external services.
6. Generated artifacts cannot become authoritative without validation and approval.
7. Dialogue cannot drive lip sync until exact words and a real clean WAV are locked.
8. Runtime outputs are versioned, hashed, reviewable, and stored outside context.

## Primary flow

```text
Context source
  -> compile and hash
  -> production plan
  -> external generation boundary
  -> render attempt
  -> technical and semantic review
  -> approval
  -> prepared edit package
  -> EDL and preview
  -> edit approval
  -> finalization and archive
  -> committed runtime continuity
```
