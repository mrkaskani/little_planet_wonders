# Lesson 1: Find the Existing Source Context

**Study time:** 15 minutes  
**Practice time:** 10 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- inspect a project before inventing new scene details;
- distinguish canonical, candidate, and generated references;
- find valid character, expression, location, music, ambience, and sound IDs;
- decide what belongs in the episode file and what should remain reusable.

---

## 2. Start with an inventory, not a prompt

A scene prompt should be the result of resolved context. It should not be the
place where you invent character identity, location geometry, or audio rules.

For the sample project, begin here:

```text
src/lpw/context/projects/riri-yoyo/
├── project.yaml
├── characters/
├── locations/
├── audios/
├── cinematography/
├── visual_style/
├── validation/
├── references.yaml
└── episodes/
```

The practical question is: **which existing authorities should this scene
select?**

---

## 3. Inspect the character authorities

Riri and Yoyo each have a canonical character file:

- [`characters/riri/character.yaml`](../../../src/lpw/context/projects/riri-yoyo/characters/riri/character.yaml)
- [`characters/yoyo/character.yaml`](../../../src/lpw/context/projects/riri-yoyo/characters/yoyo/character.yaml)

Look for these sections:

- `identity`: permanent appearance and role;
- `proportions`: shape and scale rules;
- `materials` or equivalent visual details;
- `expression_library`: valid emotions for an episode;
- `reference_images`: source assets;
- `continuity_constraints`: features that must not drift.

Do not copy all of those fields into the episode. Select the character by `id`
and select a valid emotion by its `expression_library` key.

The shared acting authority is
[`characters/acting-style.yaml`](../../../src/lpw/context/projects/riri-yoyo/characters/acting-style.yaml).
It defines:

- `intensity_scale`, such as `level_1`, `level_2`, and `level_3`;
- reusable `emotion_contracts`;
- character-specific performance signatures.

For a normal readable preschool emotion, `level_2` is the default choice. Use
`level_3` only for a brief story emphasis, not a whole scene.

---

## 4. Inspect the location authority

Locations are organized by production family. For example:

```text
locations/evening_night/
├── location.yaml
├── location-v2.yaml
├── music-profile.yaml
└── sound-profile.yaml
```

The folder name is not necessarily the public location ID. Read the top-level
`id` inside the YAML and use that exact value in the episode.

The garden greeting example deliberately selects the approved V1 location:

```yaml
location_id: kindergarten-evening-night
```

Do not switch to a V2 location merely because its filename looks newer. A file
with `status: candidate` still requires the review declared under `validation/`.
The selected version must be intentional and approved for the current use.

When inspecting a location, collect:

- stable geometry and landmarks;
- time of day and lighting direction;
- entry, exit, path, and safety boundaries;
- allowed camera zones;
- reference-image paths and status;
- ambience and music profile relationships.

---

## 5. Inspect audio and cinematography

The episode should select or summarize audio intent, while these files remain
the reusable authorities:

- [`audios/music.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/music.yaml)
- [`audios/ambience.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/ambience.yaml)
- [`audios/sound-effects.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/sound-effects.yaml)
- [`audios/voice-production.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/voice-production.yaml)
- [`audios/s2v-input-spec.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/s2v-input-spec.yaml)
- [`cinematography/camera-language.yaml`](../../../src/lpw/context/projects/riri-yoyo/cinematography/camera-language.yaml)

For each audio cue, ask:

1. Is it motivated by something visible or by the established environment?
2. Does it interfere with dialogue?
3. Does its intensity match the emotion and audience age?
4. Does it remain continuous when the camera cuts?

---

## 6. Build a scene inventory

Before writing YAML, complete this small table:

| Question | Garden greeting answer |
|---|---|
| Project | `riri-yoyo` |
| Episode | `episode-001` |
| Scene | `moonlit-garden-greeting` |
| Location | `kindergarten-evening-night` |
| Characters | `riri`, `yoyo` |
| Riri emotion | `happy`, `level_2`, `happiness` |
| Yoyo emotion | `curious`, `level_2`, `curiosity` |
| Main story action | Notice and name one warm garden light |
| Camera | Eye-level medium-wide, one gentle push-in |
| Dialogue | Three short non-overlapping lines |
| Music | Low, instrumental, ducked below dialogue |
| Ambience | Calm night garden, continuous and soft |
| Foley | One small step and one feather rustle |
| Required new reference | One clean character-location start frame |

If you cannot fill a row from approved source context or an explicit creative
decision, stop and resolve that gap before writing a provider prompt.

---

## 7. Practice activity

Choose one future scene and record:

1. the exact character IDs;
2. one valid expression key for each character;
3. one intensity level for each expression;
4. the exact location ID and approval status;
5. one camera behavior;
6. the dialogue, music, ambience, and visible Foley needs;
7. the reference images that already exist;
8. the one new reference frame that is still missing.

Do not write the final prompt yet.

---

## 8. Completion checklist

- [ ] I inspected the project before adding new details.
- [ ] I used YAML IDs, not guesses based on folder names.
- [ ] Every emotion exists in the selected character's expression library.
- [ ] Every intensity exists in the shared acting style.
- [ ] I know whether the selected location is approved or candidate.
- [ ] I separated existing source references from the new frame to generate.
- [ ] I identified conversation, music, ambience, and motivated sound effects.

