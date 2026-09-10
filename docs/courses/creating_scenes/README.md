# Creating Scenes with LPW — Crash Course

This course teaches the shortest safe path from a scene idea to resolved LPW
context that an MCP client can use for prompt and reference-image planning.

The working example is Riri and Yoyo's moonlit garden greeting in
[`episode-001`](../../../src/lpw/context/projects/riri-yoyo/episodes/episode-001/episode.yaml).
It includes a location, two characters with emotions, conversation, music,
ambience, sound effects, camera direction, and an S2V reference plan.

**Total study time:** about 130 minutes  
**Practice time:** about 140 minutes

---

## What you will create

By the end of the course, you will be able to create this chain:

```text
existing project authorities
  -> episode.yaml
  -> scene declaration
  -> resolved character + emotion + location context
  -> Phase 1: local conversation + music + effects
  -> Phase 1: manually created scene-reference image
  -> Phase 1 approval and hash lock
  -> Phase 2: clean dialogue + approved image -> Wan S2V
  -> Phase 2: add music + ambience + effects in the edit
  -> Wan 2.2 render attempt
  -> Qwen VL frame review
  -> bounded Wan 2.2 repair
  -> continuity review and final approval
```

The episode file selects the current creative state. It does not duplicate the
whole project. LPW resolves the selected IDs against reusable character,
acting, location, audio, camera, visual-style, and safety authorities.

---

## Course map

1. [Find the existing source context](lesson_01_find_the_existing_context.md)
2. [Write the episode and scene YAML](lesson_02_write_the_episode_and_scene_yaml.md)
3. [Resolve the scene locally and through MCP](lesson_03_resolve_the_scene_context.md)
4. [Build the creative prompt and S2V start frame](lesson_04_build_the_prompt_and_s2v_reference.md)

### Required production phases

1. [Phase 1 — Create and approve local audio and the manual scene reference](phase_01_create_audio_and_scene_reference.md)
2. [Phase 2 — Generate S2V from clean dialogue and the approved image](phase_02_generate_s2v_and_final_mix.md)

### Review and repair

5. [Review, approve, and hand off the scene](lesson_05_review_approve_and_handoff.md)
6. [Find and repair bad frames with Qwen VL and Wan 2.2](lesson_06_qwen_vl_wan_repair_and_continuity.md)

Complete the lessons in order the first time. After that, use Lessons 2 through
6 as a repeatable scene-production and repair checklist.

---

## Prerequisites

- Python 3.11 or newer
- The repository installed as described in [Getting started](../../getting-started.md)
- Basic YAML familiarity
- Approved or candidate project references already stored inside the project
- An MCP host configured to run the `lpw` stdio server, if you want to practice
  the MCP steps

You do **not** need an image API key for this course. The project owner creates
the S2V scene-reference image manually and registers the selected local file.

---

## Source context versus generated output

Keep these two categories separate:

| Source context | Runtime or generated output |
|---|---|
| Character identity YAML | Generated character-location composite |
| Location YAML and approved references | Image or video candidates |
| Episode and scene intent | Compiled provider prompt |
| Dialogue, music, and sound intent | Rendered WAV and music files |
| Reference and approval requirements | Review records and final approvals |

Source YAML belongs under:

```text
src/lpw/context/projects/<project-id>/
```

Generated media and production evidence belong in the configured runtime,
render, edit, or archive locations. A generated image must never silently
replace its authoritative source YAML or become approved merely because it was
generated successfully.

---

## Current implementation boundary

LPW currently supports the local portion of this course:

- loading an episode from its episode path;
- resolving each selected character's complete identity YAML;
- resolving the selected expression, acting intensity, and emotion contract;
- resolving the episode's default location;
- returning resolved context through Python or MCP;
- hashing the resolved context for reproducibility;
- creating local cloned conversations when the externally managed Qwen3-TTS
  runtime and approved voice references are installed;
- creating local music and effects when the externally managed Stable Audio 3
  runtime is installed;
- preparing and locking exact dialogue plus sound and music cue sheets.

The scene-reference image is a manual project-owner deliverable. Lesson 4
teaches how to compile the prompt and source-reference package, then register the
selected local image with provenance, a hash, and explicit human approval. LPW
does not require or plan an automated image-provider adapter for this workflow.

Wan S2V policy and workflow bindings are declared, but the real S2V workflow,
provider execution, and model artifacts must be supplied and enabled by the
operator. The two phase guides therefore distinguish commands that exist now
from provider boundaries that remain planned or disabled.

The editing stack also has assisted edit planning, immutable attempts, Wan 2.2
review cards, and continuity policies. The Qwen VL frame-analysis adapter and
automatic Qwen-to-Wan repair execution are a required next stage, not a completed
provider integration. Lesson 6 defines their input, output, and safety contract.

The two production phase guides make the audio boundary explicit. Phase 1 may
create conversation turns, music, ambience, and effects at the same time, but
Phase 2 sends only one speaker's approved clean dialogue WAV to each S2V unit.
The music, ambience, and effects remain separate stems and are mixed after the
video has passed review.

---

## Definition of done

A scene is ready for a generation handoff only when:

- [ ] The episode and scene IDs are stable.
- [ ] Every selected character and emotion resolves from canonical YAML.
- [ ] The location ID resolves to the intended approved version.
- [ ] Dialogue, listener behavior, music, ambience, and visible sound cues agree.
- [ ] The shot has one readable action and one camera behavior.
- [ ] The reference plan names the exact source assets and required new frame.
- [ ] The S2V input is one clean scene frame, not a model sheet or collage.
- [ ] Every speaking S2V unit has exactly one speaker and one clean dialogue WAV.
- [ ] Music, ambience, Foley, and effects are excluded from S2V conditioning.
- [ ] Phase 1 audio and image outputs are approved and locked by hash.
- [ ] The context hash has been recorded with the planned generation job.
- [ ] A human has approved the story, dialogue, and S2V start frame.
- [ ] Qwen VL records an explicit pass or identifies exact frame ranges and
      violated context rules for every finding.
- [ ] Any Wan repair preserves character, location, state, voice, music, and
      boundary continuity.
- [ ] Repaired footage has passed a new technical, semantic, and continuity review.
- [ ] `production_authorized` is changed only by the responsible human.
