# Phase 2: Generate S2V and Build the Final Mix

**Study time:** 15 minutes  
**Practice time:** 20 minutes

---

## 1. Phase objective

Phase 2 uses the approved image and clean dialogue turns from Phase 1 to create
Wan 2.2 S2V segments. After visual review, it edits the segments together and
adds the locked music, ambience, Foley, and sound effects.

Phase 2 never sends the combined conversation or final audio mix into S2V.

---

## 2. The S2V input pair

Every speaking generation unit receives exactly this pair:

```text
one approved coherent scene/start image
  + one approved clean dialogue WAV from one speaker
  = one Wan 2.2 S2V speaking segment
```

Held out until editing:

- music;
- ambience;
- Foley;
- sound effects;
- the combined multi-speaker conversation preview;
- decorative or background vocals.

This prevents environmental sounds or music rhythm from influencing mouth,
gesture, facial, or body motion.

---

## 3. Split conversation into speaking units

The sample conversation becomes three S2V units:

| Segment | Speaker | S2V audio | Listener state |
|---|---|---|---|
| `riri-line-001` | Riri | Locked Riri turn 001 | Yoyo attentive, beak closed |
| `yoyo-line-002` | Yoyo | Locked Yoyo turn 002 | Riri attentive, mouth closed |
| `riri-line-003` | Riri | Locked Riri turn 003 | Yoyo understanding, beak closed |

Each unit has one speaker. The listener may remain visible but must not mouth the
speaker's words.

For the first unit, use the approved Phase 1 scene-reference image. For the next
unit, prefer the previous segment's approved stable end frame so pose, gaze,
camera, lighting, and background do not reset. A deliberate cut may instead use
a separately approved clean start frame.

---

## 4. Run the Phase 2 preflight

Block S2V unless:

- the Phase 1 manifest is approved;
- all inputs share the current context hash;
- the image path and SHA-256 match the approved scene reference;
- the dialogue WAV path and SHA-256 match its lock record;
- transcript and word timing match exactly;
- the audio is one-speaker, dry, mono, 48 kHz, and 24-bit;
- the character's mouth or beak is visible and resting in the start frame;
- the requested duration covers leading silence, speech, and final settle;
- the character, location, camera, action, and continuity locks are present;
- the selected Wan workflow and frame count are valid.

---

## 5. Compile one S2V job per turn

```yaml
wan_s2v_job:
  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  segment_id: riri-line-001
  context_hash: <phase-1-context-hash>
  phase_1_approval_hash: <phase-1-approval-hash>

  mode: s2v
  model: wan2.2-s2v-14b
  inputs:
    image:
      reference_id: episode-001-moonlit-garden-greeting-s2v-start-frame-v001
      path: <approved-scene-image>
      sha256: <image-hash>
    audio:
      role: final-s2v-conditioning-audio
      speaker: riri
      path: <locked-riri-line-001-wav>
      sha256: <audio-hash>
      transcript: "Hi, Yoyo! Look at the warm light."
      transcript_hash: <transcript-hash>

  performance:
    speaker_emotion: happy
    intensity: level_2
    speaker_action: one-small-paw-lift-toward-the-warm-light
    listener: yoyo
    listener_state: attentive-closed-beak-and-gaze-on-the-light

  preserve:
    - both-character-identities-and-relative-scale
    - wardrobe-colors-materials-and-markings
    - approved-location-geometry-and-lighting
    - camera-side-framing-and-gentle-push-in
    - ground-contact-and-eye-lines

  excluded_audio:
    - combined-conversation
    - music
    - ambience
    - foley
    - sound-effects

  output:
    creates_new_attempt: true
    human_review_required: true
```

`compile_dialogue_lip_sync_context` supplies the authoritative locked dialogue
path and hashes. The generation package must use those exact values rather than
a temporary conversation output.

---

## 6. Generate and review each segment

Wan execution remains provider-gated. When the real S2V ComfyUI workflow is
installed and deliberately enabled:

1. submit the approved image and locked dialogue;
2. save the exact workflow graph, bindings, seed, frame count, and provider IDs;
3. store the returned video as a new immutable attempt;
4. run technical validation;
5. run semantic and Qwen VL visual review;
6. approve a stable final frame for the next segment;
7. carry the continuity state and end frame forward;
8. proceed to the next speaker only after the predecessor passes.

The source frame, locked audio, prior attempt, and provider response are never
overwritten.

---

## 7. Handle non-speaking units correctly

S2V is for a speaking performance with locked dialogue. Use a different mode
when the unit has no dialogue:

| Unit | Preferred boundary |
|---|---|
| Silent reaction from an approved frame | I2V |
| Environment establishing shot | I2V or T2V according to identity needs |
| Draft blocking exploration | TI2V |
| Exact visible speaking performance | S2V |

Do not create fake silence audio merely to force a non-speaking shot through
S2V.

---

## 8. Reassemble dialogue and picture

After all speaking units pass:

- order them by the episode conversation;
- use hard cuts or minimal reviewed boundary blends;
- preserve natural pauses and final settles;
- keep the original locked dialogue WAVs as audio source of truth;
- verify that the video covers every word and silence event;
- verify the listener remains silent and visually secondary;
- reject duplicated motion, reset poses, lighting jumps, or background warps.

Even if the provider returns audio inside the video container, compare it with
the locked dialogue. The approved clean WAV and its hash remain authoritative.

---

## 9. Add the Phase 1 audio stems after S2V

Build the final scene mix only after picture approval:

```text
locked dialogue turns
  + continuous calm-night ambience
  + time-aligned paw step and feather rustle
  + evening-night-friendship music bed
  -> dialogue-priority final mix
```

Mixing rules:

- dialogue remains centered and highest priority;
- music ducks under speech and contains no vocals;
- ambience continues across speaker cuts;
- effects occur only on their visible action frames;
- music, ambience, and effects do not mask word onsets or endings;
- the selected Phase 1 asset hashes and timeline offsets are recorded;
- picture-only repairs reuse the same approved audio stems.

Finalization validates sample rate, loudness, true peak, duration, sync, missing
audio, and continuity before committing runtime state.

---

## 10. Use Qwen VL repair without breaking audio

If Qwen VL identifies bad frames:

1. keep the Phase 1 image, dialogue, music, ambience, and effect locks;
2. send only the failing valid segment back to Wan;
3. use the same locked clean dialogue if the visible mouth performance failed;
4. do not send the final mix as S2V conditioning;
5. reinsert the repaired segment into a new edit version;
6. reapply the same approved Phase 1 audio stems and offsets;
7. recheck both visual boundaries, lip timing, voice hashes, and mix continuity;
8. require new human approval.

If the dialogue WAV itself is wrong, create and approve a new dialogue version,
then regenerate every S2V segment that depends on its old hash.

---

## 11. Phase 2 completion manifest

```yaml
phase_2_result:
  context_hash: <resolved-context-hash>
  phase_1_approval_hash: <phase-1-approval-hash>
  s2v_segments:
    - segment_id: riri-line-001
      input_image_sha256: <hash>
      input_audio_sha256: <hash>
      transcript_hash: <hash>
      video_attempt_id: attempt-0001
      video_sha256: <hash>
      approved_end_frame_sha256: <hash>
      status: approved
  final_mix:
    dialogue_hashes: [<hash>, <hash>, <hash>]
    music_sha256: <hash>
    ambience_sha256: <hash>
    sound_effect_sha256: [<hash>, <hash>]
    timeline_hash: <hash>
    status: awaiting-human-approval
  qwen_vl_review_id: <review-id>
  production_authorized: false
```

---

## 12. Phase 2 completion checklist

- [ ] Every speaking unit used exactly one clean dialogue WAV and one approved image.
- [ ] The combined conversation, music, ambience, and effects were excluded from S2V.
- [ ] Each segment uses the correct speaker identity and listener state.
- [ ] Later segments inherit an approved end frame or use a separately approved cut frame.
- [ ] Every output is an immutable attempt with provider and hash provenance.
- [ ] Technical, semantic, Qwen VL, and continuity review passed.
- [ ] The final edit reuses the approved Phase 1 audio stems.
- [ ] Dialogue remains clear and the audio mix remains continuous across cuts.
- [ ] Repairs create new versions and reuse the locked audio when it is not defective.
- [ ] Human approval is required before final production authorization.

