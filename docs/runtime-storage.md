# Runtime storage

## Directory ownership

```text
runtime/
  audio/                 dialogue packages, locked WAVs, and approvals
  continuity/            committed scene continuity
  extensions/            shot-extension plans and segment snapshots
  editing/               optional runtime editorial state

renders/
  <story>/<scene>/<shot>/attempt-NNNN/
  <story>/<scene>/releases/release-NNNN/

edits/
  <project>/<scene>/prepared/vNNN/
  <project>/<scene>/vNNN/

archive/
  <project>/<scene>/vNNN/
```

## Atomic metadata writes

JSON and YAML metadata are written to a temporary file in the destination
directory and atomically replaced. This prevents partially written manifests from
appearing valid after interruption.

## Immutability

- Context source files are never runtime destinations.
- Attempt, dialogue, edit, extension, and release versions are monotonically new.
- Approval files cannot be overwritten.
- Hashes bind decisions to exact context and artifacts.
- Final continuity is committed only after successful export.

## Recovery

Failed or rejected attempts remain available for diagnosis. Create a new version
for repaired output instead of editing historical evidence in place.
