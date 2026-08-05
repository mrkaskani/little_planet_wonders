# Context system

## Normalized hierarchy

The normalized compiler reads:

```text
project.yaml
stories/<story>.yaml
scenes/<scene>.yaml
shots/<scene>/<shot>.yaml
props/<prop>.yaml
wardrobe/<profile>.yaml
continuity/<scene>/{scene-state,shot-state}.yaml
production/<scene>.yaml
validation/{defaults,scenes/<scene>}.yaml
tools/{generation-tools,editing-models,wan22-models}.yaml
```

`ContextCompiler.compile_scene()` verifies IDs, relationships, referenced files,
unique shots, wardrobe, props, and continuity. It applies stable defaults without
rewriting source YAML.

## Nested cinematic context

The nested classroom context contains studio, project, character, location,
audio, sequence, scene, shot, segment, editing, export, and continuity policies.
`load_project_context()` normalizes flat and nested variants and appends a stable
context hash.

## Versioned inheritance

`ContextChainResolver` accepts pinned URIs such as:

```text
cinema://studio/cinematic-defaults@1
cinema://projects/classroom@1
cinema://projects/classroom/scenes/rooftop-confrontation@1
cinema://projects/classroom/scenes/rooftop-confrontation/shots/shot-004@1
```

Supported mechanisms:

- `extends`: recursively inherit pinned parents;
- `imports`: load reusable context into a named namespace;
- `overrides`: make explicit local changes;
- `patches`: apply `add`, `replace`, or `remove` JSON-pointer operations.

The resolver detects cycles, rejects `@latest`, constrains filesystem paths, and
enforces immutable fields declared by merge policy.

## Merge policy

- Scalars: child override.
- Dictionaries: recursive merge.
- Constraints, forbidden values, and references: append unique.
- Character and prop lists: merge by `id`.
- Other lists: child replacement.

## Reproducibility hashes

Generation and extension flows store:

- source or base context hash;
- runtime-state hash;
- compiled-segment or package hash;
- media SHA-256 where real files exist;
- approval and release manifest hashes.

Hashes identify the exact context and state used by an artifact. They do not
replace human approval or media validation.
