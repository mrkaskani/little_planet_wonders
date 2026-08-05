# Architecture

## Package ownership

| Package | Responsibility |
| --- | --- |
| `lpw.context` | Load, validate, merge, inherit, snapshot, and hash context |
| `lpw.generation` | Compile Wan packages, plan scenes, adapt workflows, and extend shots |
| `lpw.audio` | Compile dialogue, voice locks, ambience, effects, music, and mix rules |
| `lpw.validation` | Store render attempts, run checks, record reviews, and create releases |
| `lpw.editing` | Prepare takes, build EDLs, render previews, finalize, and archive |
| `lpw.integrations` | Talk to explicitly configured external systems such as ComfyUI |
| `lpw.mcp` | Adapt domain services into MCP resources and controlled tools |
| `lpw.utils` | Provide atomic I/O, hashing, identifiers, merges, and references |

The MCP layer contains no independent production policy. It validates and adapts
arguments, then delegates to domain services.

## Context and runtime boundary

```text
src/lpw/context_data + src/lpw/context
                    |
                    v
          deterministic compilation
                    |
                    v
    package/context/runtime hashes and snapshots
                    |
                    v
runtime/  renders/  edits/  archive/
```

Context is the source of truth. Runtime state is evidence of what happened.
Continuity becomes authoritative only after the corresponding approval or final
export succeeds.

## Four production chains

Long-form work maintains parallel state:

- semantic: story, characters, locations, props, and wardrobe;
- visual: frames, camera, lighting, identity, and visible state;
- audio: exact dialogue, ambience, music position, Foley, and effects;
- editorial: selected takes, trims, transitions, warnings, and timeline position.

Shot-extension continuity is event sourced. Each approved segment records a small
delta and a cumulative output state; the next segment receives the approved stable
end frame and cumulative state.

## External execution boundary

LPW can compile and validate without external services. Actual voice, image,
audio, or Wan execution requires an operator-enabled provider. Provider output is
never accepted merely because a request completed: it enters a render attempt and
must pass technical and semantic review.

## Failure behavior

- Missing required context raises a context error.
- Unsafe identifiers or escaping paths are rejected.
- Circular or unpinned inheritance is rejected.
- Disabled providers block real execution but not dry runs.
- Missing workflow exports fail clearly; LPW does not fabricate graphs.
- Blocking validation prevents approval and release.
- Existing immutable approval decisions cannot be overwritten.
