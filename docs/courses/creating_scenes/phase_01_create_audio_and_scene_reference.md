# Phase 1: Create Audio and the Scene Reference

**Study time:** 20 minutes  
**Practice time:** 25 minutes

---

## 1. Phase objective

Phase 1 creates and approves every external asset that Phase 2 will consume:

- one clean local dialogue WAV per speaker turn;
- a combined conversation preview for listening and editorial planning;
- local music, ambience, Foley, and sound-effect stems;
- one coherent scene-reference image created manually by the project owner;
- hashes, manifests, and human approval records for every selected asset.

Phase 1 does not generate Wan video.

---

## 2. Required outputs

| Asset | Creation boundary | Used directly by S2V? |
|---|---|:---:|
| One clean dialogue turn | Local Qwen3-TTS voice clone | Yes |
| Combined multi-speaker conversation | Local conversation assembler | No |
| Scene music | Local Stable Audio 3 | No; final edit only |
| Ambience | Approved local asset or local generator | No; final edit only |
| Foley and sound effects | Local Stable Audio 3 | No; final edit only |
| Clean scene-reference image | Manual project-owner creation and handoff | Yes |

The combined `conversation.wav` is useful for listening to pacing, but it cannot
be S2V conditioning because it contains more than one speaker. Use the individual
turn WAVs under `turns/`.

---

## 3. Freeze the source context first

Resolve the episode and record its context hash before generation:

```bash
.venv/bin/python - <<'PY'
from lpw.context.loader import load_project_context

context = load_project_context("riri-yoyo", episode_id="episode-001")
print(context["metadata"]["context_hash"])
PY
```

Every Phase 1 manifest must carry this hash. If source YAML changes materially,
resolve it again and create a new Phase 1 version rather than silently reusing
old assets.

---

## 4. Create the conversation locally

Build conversation JSON from the exact ordered episode dialogue:

```json
{
  "title": "Episode 001 — Moonlit Garden Greeting",
  "project": "riri-yoyo",
  "language": "English",
  "seed": 424242,
  "turns": [
    {
      "speaker": "riri",
      "text": "Hi, Yoyo! Look at the warm light."
    },
    {
      "speaker": "yoyo",
      "text": "Is that our garden light?"
    },
    {
      "speaker": "riri",
      "text": "Yes. It helps us see the path."
    }
  ]
}
```

Validate without loading the voice model:

```bash
scripts/qwen3_tts/generate-conversation.sh \
  /absolute/path/to/episode-001-moonlit-garden.json \
  --validate-only
```

Generate locally into a new immutable output directory:

```bash
scripts/qwen3_tts/generate-conversation.sh \
  /absolute/path/to/episode-001-moonlit-garden.json \
  --output-dir /absolute/path/to/episode-001-moonlit-garden-v001
```

The output contains:

```text
conversation.wav
manifest.json
transcript.md
turns/
  001-riri.wav
  002-yoyo.wav
  003-riri.wav
```

Review the combined conversation for pacing and speaker continuity. Review and
lock each `turns/*.wav` independently for S2V.

---

## 5. Prepare and lock each S2V dialogue turn

Each S2V dialogue asset must satisfy
[`s2v-input-spec.yaml`](../../../src/lpw/context/projects/riri-yoyo/audios/s2v-input-spec.yaml):

- exactly one speaker;
- exact approved transcript;
- dry dialogue only;
- mono WAV, PCM 24-bit, 48 kHz;
- no music, ambience, Foley, effects, reverb, or background vocals;
- 150 ms leading silence and 250 ms final settle unless reviewed otherwise;
- reviewed pronunciation, identity, emotion, and listening comfort;
- audio and transcript hashes.

Normalize a reviewed turn when necessary:

```bash
ffmpeg -i /absolute/path/to/001-riri.wav \
  -ar 48000 -ac 1 -c:a pcm_s24le \
  /absolute/path/to/001-riri-s2v-v001.wav
```

Use the MCP workflow for each turn:

```text
prepare_exact_dialogue(...)
  -> generate or select the local turn WAV
  -> human review
  -> lock_exact_dialogue(...)
  -> compile_dialogue_lip_sync_context(...)
```

`lock_exact_dialogue` copies the approved WAV into versioned runtime storage and
records its SHA-256. A transcript, timing, or audio change creates a new dialogue
version and invalidates downstream S2V video.

---

## 6. Create sound effects locally

Compile a cue sheet before generating assets so each effect has a visible source,
story purpose, time, distance, level, and safety rule:

```text
compile_sound_cue_sheet(
  project_id="riri-yoyo",
  scene_id="moonlit-garden-greeting",
  shot_id="shot-001",
  location_id="kindergarten-evening-night",
  cues=[...],
  dialogue_present=true
)
```

Then create declared effects through the local Stable Audio 3 boundary:

```bash
python3 scripts/orchestrator/audio_generator.py sfx \
  "tiny soft paw step on a safe stone garden path, isolated Foley, no voice" \
  --seconds 2 \
  --seed 5152 \
  --output /absolute/path/to/riri-small-paw-step-v001.wav
```

Create the feather rustle separately. Keep both effects isolated so the editor
can place, trim, and mix them without altering dialogue.

---

## 7. Create music locally

Compile the music cue sheet from the selected project and location profiles:

```text
compile_music_cue_sheet(
  project_id="riri-yoyo",
  episode_id="episode-001",
  scene_id="moonlit-garden-greeting",
  cues=[...],
  dialogue_present=true
)
```

Generate the instrumental scene bed locally:

```bash
scripts/orchestrator/soundtrack.sh \
  "very soft nighttime friendship underscore, sparse warm piano, gentle clarinet, subtle strings, quiet acoustic guitar plucks, calm preschool-safe, instrumental, dialogue space, no vocals" \
  --seconds 12 \
  --seed 6201 \
  --output /absolute/path/to/evening-night-friendship-v001.wav
```

The result must preserve the `soft-kids-pop` project identity and the
`evening-night-friendship` location state. Review it for dialogue space, gentle
energy, motif consistency, loop or ending quality, and lack of vocals.

Once approved, record its path and SHA-256 in runtime continuity. A later visual
repair reuses this exact stem and timeline offset.

---

## 8. Select or create ambience locally

Use the declared `kindergarten_exterior_garden` ambience with the `calm-night`
state. Prefer an approved existing asset. Generate a new version only when the
required state does not exist or fails review.

Ambience must:

- preserve night-garden identity;
- remain stable beneath dialogue;
- avoid distinct unplanned voices or frightening animals;
- continue across cuts instead of restarting per speaker;
- receive an immutable path and hash after approval.

---

## 9. Create and register the scene-reference image manually

Use the resolved character expressions, approved character references, active
location geometry, camera, lighting, and exact starting state while creating the
image manually. The delivered image must be one coherent frame with both
characters—not a board or collage.

Copy the selected image into the project runtime or asset handoff directory,
then record a manifest before it is approved:

```yaml
manual_scene_reference_handoff:
  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  context_hash: <resolved-context-hash>
  creator: project-owner
  creation_method: manual
  source_references:
    - id: riri-neutral-full-body-v001
      sha256: <asset-hash>
    - id: yoyo-neutral-full-body-v001
      sha256: <asset-hash>
    - id: kindergarten-evening-night-primary-master-v001
      sha256: <asset-hash>
  output_id: episode-001-moonlit-garden-greeting-s2v-start-frame-v001
  local_path: <absolute-or-project-relative-image-path>
  output_sha256: <asset-hash>
  output_requirements:
    - one-coherent-single-frame-scene
    - exact-two-characters
    - both-identities-and-relative-scale-preserved
    - approved-location-geometry-and-night-lighting
    - both-mouths-or-beaks-at-rest
    - no-text-label-watermark-or-duplicate-character
  provenance_note: <how-and-when-the-image-was-created>
  approval_status: awaiting-human-review
```

Do not infer approval from the presence of a file. Verify its identity,
composition, location geometry, lighting, character scale, starting mouth/beak
state, and technical readability, then record explicit human approval.

---

## 10. Write the Phase 1 lock manifest

Phase 1 finishes with a runtime manifest similar to:

```yaml
phase_1_lock:
  phase_version: 1
  context_hash: <resolved-context-hash>
  dialogue_turns:
    - line_order: 1
      speaker: riri
      transcript_hash: <hash>
      audio_path: <locked-clean-wav>
      audio_sha256: <hash>
      status: approved
  combined_conversation:
    path: <conversation-preview-wav>
    role: pacing-review-only-not-s2v-conditioning
  music:
    cue_id: evening-night-friendship
    path: <approved-music-wav>
    sha256: <hash>
  ambience:
    profile: kindergarten_exterior_garden
    state: calm-night
    path: <approved-ambience-wav>
    sha256: <hash>
  sound_effects:
    - cue_id: riri-small-paw-step
      path: <approved-sfx-wav>
      sha256: <hash>
  scene_reference:
    reference_id: episode-001-moonlit-garden-greeting-s2v-start-frame-v001
    path: <approved-scene-image>
    sha256: <hash>
  human_approval:
    approved: true
    reviewer: <reviewer>
    approval_hash: <hash>
```

Do not start Phase 2 while any required value is missing, unreviewed, or tied to
a different context hash.

---

## 11. Phase 1 completion checklist

- [ ] The resolved context hash is recorded.
- [ ] Exact episode dialogue became one clean WAV per speaker turn.
- [ ] The combined conversation is marked review-only, not S2V conditioning.
- [ ] Every dialogue turn is 48 kHz, 24-bit, mono, dry, and hash-locked.
- [ ] Music, ambience, and every effect are separate local stems.
- [ ] Music and effects were reviewed against their declared profiles and cues.
- [ ] The manually created image uses approved character and location references.
- [ ] The selected image is one clean, coherent, approved scene frame.
- [ ] Every selected file has a path, hash, version, and human approval.
- [ ] Phase 2 remains blocked until the Phase 1 lock is complete.
