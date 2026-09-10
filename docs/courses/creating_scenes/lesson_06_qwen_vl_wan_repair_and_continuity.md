# Lesson 6: Find and Repair Bad Frames with Qwen VL and Wan 2.2

**Study time:** 20 minutes  
**Practice time:** 20 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- use resolved scene context as Qwen VL's visual review contract;
- locate a defect as an exact frame and timecode range;
- turn a review finding into the smallest safe Wan 2.2 repair job;
- preserve continuity inside a shot and across scenes and episodes;
- protect voice, dialogue, music, ambience, identity, and location during repair;
- keep automated analysis separate from human approval.

---

## 2. The repair loop

Qwen VL does not directly rewrite video pixels. Its responsibility is to inspect
the rendered video, compare visible evidence with the resolved scene contract,
and return a structured defect report. Wan 2.2 then generates a replacement
segment from approved anchors and the same locked context.

```text
approved context + approved references + rendered attempt
  -> extract technical metadata and review frames
  -> Qwen VL compares frames with the context contract
  -> locate first bad frame and last bad frame
  -> classify the violated rule and repair strategy
  -> compile a bounded Wan 2.2 replacement segment
  -> validate and splice the new immutable attempt
  -> Qwen VL rechecks the repair and both boundaries
  -> deterministic audio and continuity checks run
  -> human approves or rejects the new edit version
```

The loop should repair the smallest valid interval. It must not regenerate a
whole scene when a short segment can be safely replaced.

---

## 3. Give Qwen VL a resolved review contract

Do not ask Qwen VL only, “Find bad frames.” Supply the expected state and its
provenance:

```yaml
qwen_vl_review_input:
  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  shot_id: shot-001
  attempt_id: attempt-0001
  context_hash: <resolved-context-hash>
  generation_package_hash: <package-hash>
  source_video:
    path: <immutable-render-path>
    sha256: <video-hash>
    frame_rate: 24
    frame_count: <measured-frame-count>

  expected_story_state:
    action: riri-points-out-the-warm-light-and-yoyo-follows-her-gaze
    start_state: both-standing-securely-with-mouth-and-beak-at-rest
    end_state: both-looking-at-the-light-with-calm-understanding
    exact_character_count: 2

  character_locks:
    riri:
      character_id: riri
      identity_reference_id: riri-neutral-full-body-v001
      identity_reference_sha256: <asset-hash>
      expression: happy
      intensity: level_2
      immutable_fields:
        - species
        - body-and-head-shape
        - proportions-and-scale
        - face-eye-and-marking-design
        - permanent-colors-and-materials
        - wardrobe-and-accessories
    yoyo:
      character_id: yoyo
      identity_reference_id: yoyo-neutral-full-body-v001
      identity_reference_sha256: <asset-hash>
      expression: curious
      intensity: level_2
      immutable_fields:
        - species
        - body-and-head-shape
        - proportions-and-scale
        - face-eye-beak-and-marking-design
        - permanent-colors-and-materials
        - wardrobe-and-accessories

  location_lock:
    location_id: kindergarten-evening-night
    reference_id: kindergarten-evening-night-primary-master-v001
    reference_sha256: <asset-hash>
    preserve:
      - building-entrance-path-and-tree-geometry
      - practical-light-position
      - blue-night-and-warm-light-balance

  shot_locks:
    framing: medium-wide-full-character-readable
    camera_angle: preschool-eye-level
    camera_behavior: slow-gentle-push-in
    screen_direction: <resolved-direction>

  boundary_anchors:
    previous_approved_end_frame:
      path: <previous-frame-path>
      sha256: <frame-hash>
    approved_start_frame:
      path: <start-frame-path>
      sha256: <frame-hash>
    expected_end_state_reference: <state-or-reference-id>

  review_cards:
    source: wan22-review-cards.yaml
    ordered_checks:
      - structure
      - composition
      - subject-count
      - identity-and-anatomy
      - motion-and-contact
      - temporal-stability
      - materials-and-lighting
      - fine-detail
      - audio-alignment-when-applicable
```

Pass resolved values rather than forcing the analyzer to rediscover project
rules from filenames. The IDs and hashes ensure it reviews the same creative
state that produced the render.

---

## 4. Use two-pass frame localization

Analyzing only a few thumbnails can miss one-frame defects. Analyzing every
frame at maximum detail is expensive and can lose temporal context. Use two
passes:

### Pass A: coarse scan

- read the real frame rate and frame count with FFprobe;
- sample the full shot at a configurable interval;
- always include the first frame, last frame, dialogue boundaries, shot cuts,
  and known action contacts;
- compare adjacent samples for identity, geometry, color, and state drift;
- mark suspicious time windows.

### Pass B: dense inspection

- decode every frame in each suspicious window;
- include stable frames before and after the window;
- locate the first failing frame and last failing frame;
- identify whether the failure is isolated, progressive, or persistent;
- attach representative evidence frames and confidence.

Frame numbers are authoritative for repair. Timecodes are derived from the
measured frame rate and are included for editors and reviewers.

---

## 5. Require structured Qwen VL findings

Qwen VL should return machine-validated data, not a free-form paragraph:

```yaml
qwen_vl_review_result:
  review_id: qwen-vl-review-0001
  model: <pinned-qwen-vl-model>
  model_revision: <pinned-revision>
  context_hash: <resolved-context-hash>
  source_video_sha256: <video-hash>
  status: repair-required

  findings:
    - defect_id: defect-001
      first_bad_frame: 97
      last_bad_frame: 108
      first_bad_timecode: "00:00:04:01"
      last_bad_timecode: "00:00:04:12"
      evidence_frames: [96, 97, 102, 108, 109]
      category: identity-and-anatomy
      violated_contract:
        authority: characters/yoyo/character.yaml
        rule: preserve-beak-shape-and-face-markings
      observation: yoyo-beak-widens-and-face-mask-shifts-during-head-turn
      severity: blocking
      confidence: 0.94
      temporal_pattern: progressive-then-recovers
      suggested_action: regenerate-bounded-segment
      preserve_before_frame: 96
      preserve_after_frame: 109

  reviewer_limitations:
    - visual-analysis-does-not-prove-voice-identity
    - visual-analysis-does-not-prove-music-or-audio-continuity
  approval_status: machine-finding-awaiting-repair-and-human-review
```

The report must cite the violated context authority. “Looks strange” is not an
actionable repair instruction.

---

## 6. Route the smallest correct repair

Use the defect class to choose a repair:

| Finding | Preferred action |
|---|---|
| Unstable frames only at a clip edge | Trim if action, dialogue, and handles remain intact |
| Isolated identity or anatomy drift | Regenerate a bounded segment with identity locks |
| Wrong source-frame pose or anatomy | Replace and approve the source frame, then regenerate |
| Location geometry or lighting drift | Regenerate with location reference and geometry locks |
| Too many actions or competing camera cues | Split or simplify the segment |
| Wrong mouth movement with correct locked audio | Regenerate the S2V speaking interval |
| Wrong dialogue audio | Correct and lock audio, then regenerate the affected speaking interval |
| Wrong music, ambience, or mix | Repair the audio stem or edit; do not regenerate picture unnecessarily |
| Story or continuity contradiction | Return to context planning; do not hide it with a local visual patch |

The repository's supported Wan 2.2 modes do not imply arbitrary in-place editing
of individual encoded frames. A safe “send it back to Wan” operation normally
means generating a new segment around the bad interval, then replacing that
interval in a new edit version.

---

## 7. Build the Wan 2.2 repair job

The repair job must inherit the original package and explicitly lock what cannot
change:

```yaml
wan_repair_job:
  repair_id: repair-0001
  source_attempt_id: attempt-0001
  source_video_sha256: <video-hash>
  qwen_vl_review_id: qwen-vl-review-0001
  defect_ids: [defect-001]

  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  shot_id: shot-001
  context_hash: <same-resolved-context-hash>
  generation_package_hash: <same-or-versioned-package-hash>

  repair_window:
    first_bad_frame: 97
    last_bad_frame: 108
    stable_frame_before: 96
    stable_frame_after: 109
    handles_before: <configured-handle-count>
    handles_after: <configured-handle-count>
    generated_frame_count: <valid-wan-frame-count>

  wan_mode: s2v
  conditioning:
    approved_start_anchor: <stable-frame-before-path>
    target_end_state: <state-at-stable-frame-after>
    locked_dialogue_audio: <approved-clean-dialogue-path>
    dialogue_audio_sha256: <audio-hash>
    transcript_sha256: <transcript-hash>
    character_reference_ids:
      - riri-neutral-full-body-v001
      - yoyo-neutral-full-body-v001
    location_reference_id: kindergarten-evening-night-primary-master-v001

  repair_instruction: >-
    Preserve all approved motion before and after the repair window. Recreate
    Yoyo's gentle head turn with the canonical beak shape and face markings.
    Preserve character scale, ground contact, gaze target, location geometry,
    lighting, camera trajectory, exact dialogue timing, and the target end state.

  unchanged:
    - character-identity-and-relative-scale
    - wardrobe-colors-materials-and-accessories
    - location-geometry-light-sources-and-time-of-day
    - prop-state-and-ownership
    - camera-path-and-screen-direction
    - dialogue-file-transcript-timing-and-voice
    - music-ambience-and-sound-effect-stems

  creates_new_attempt: true
  overwrite_source_attempt: false
  human_approval_required: true
```

Wan frame counts and duration must satisfy the selected workflow's constraints.
If the defect is shorter than a valid generation unit, enlarge the repair window
to stable action boundaries rather than requesting an invalid or discontinuous
micro-generation.

---

## 8. Continuity is a hierarchy of locks

Continuity must be checked at four levels:

| Level | Examples of locked information |
|---|---|
| Series | Character identity, body shape, proportions, permanent colors, voice identity, recurring music language |
| Episode | Wardrobe, selected voice references, music theme or motif version, story-day state, persistent props and emotional arc |
| Scene | Location and lighting state, ambience bed, character condition, current emotion, prop placement, screen direction |
| Shot or segment | Exact pose, gaze, hand or paw occupancy, mouth state, camera, dialogue timing, start frame, end frame |

Lower levels may change only fields explicitly authorized by the story. A repair
inherits every higher-level lock and changes only its declared bad interval.

### Character continuity

Compare the repaired segment against:

- canonical character YAML;
- approved identity and generation references with hashes;
- approved two-character scale relationship;
- current expression and intensity;
- wardrobe, accessory, cleanliness, wetness, and condition state;
- the stable frame before and after the repair.

“Same character” means the same shape language, proportions, face, eyes,
markings, colors, materials, wardrobe, scale, and movement signature—not merely
the same name in the prompt.

### Voice and dialogue continuity

Lock:

- `character_id` and voice-profile ID;
- approved voice-reference ID and hash;
- exact dialogue text and transcript hash;
- final clean dialogue WAV and hash;
- sample rate, timing, pauses, emotion, pronunciation, and loudness target.

For a picture-only repair, reuse the original approved dialogue stem. For an S2V
mouth repair, use the exact same locked clean dialogue audio unless the audio was
the diagnosed failure.

### Music and sound continuity

Lock:

- cue ID, theme or motif ID, version, and audio-file hash;
- timeline offset, beat or sync points, and dialogue-ducking automation;
- ambience profile, state, and room-tone continuity;
- sound-effect cue IDs and their visible action anchors.

Wan should repair picture against the existing audio timing. It should not
silently regenerate the score, ambience, Foley, or character voice.

### Location and camera continuity

Lock the exact location ID, approved reference version and hash, geometry,
landmarks, time of day, practical-light positions, camera side, screen direction,
lens feel, and camera trajectory. Check the first and last repaired frames
against their untouched neighbors.

---

## 9. Understand Qwen VL's audio boundary

Qwen VL can review visible mouths, expressions, composition, identity, motion,
and frame-to-frame continuity. A visual-language model cannot prove from silent
frames that the same voice, music master, or ambience file was used.

Audio continuity therefore needs deterministic and audio-aware evidence:

- compare audio and transcript hashes;
- verify that the same approved stems and timeline offsets were reused;
- use speech, speaker, music, and audiovisual analyzers when configured;
- pass their structured results to the repair planner;
- use Qwen VL for visible lip timing and visual response, not voice fingerprinting.

This division prevents a confident visual report from making an unsupported
claim about sound.

---

## 10. Recheck the repair before insertion

A replacement segment passes only when:

1. technical validation passes;
2. Qwen VL reports no blocking visual finding in the repair window;
3. the frame before the splice matches the replacement entrance;
4. the replacement exit matches the frame after the splice;
5. no duplicate, jump, reset, foot slide, prop teleport, or lighting pulse appears;
6. identity, shape, scale, wardrobe, location, and camera locks pass;
7. dialogue and audio hashes match the repair job;
8. mouth motion and silence behavior align when applicable;
9. music, ambience, and sound-effect continuity pass;
10. a human approves the repaired attempt and new edit preview.

Never overwrite the original render. Store the repair as a new attempt and the
splice as a new edit version so rejection remains recoverable.

---

## 11. Current implementation boundary

The repository already declares or implements parts of this design:

- reusable ordered Wan review cards;
- technical and semantic render validation;
- immutable attempts and approvals;
- continuity-aware segment chaining;
- assisted take selection and preview editing;
- post-edit repair notes that stop at `changes-requested` when a provider is
  required;
- disabled externally managed analysis and planning roles.

It does not yet contain an enabled Qwen VL adapter that performs the two-pass
frame scan or automatically submits bounded repair jobs to Wan 2.2. Until that
adapter, schema validation, and tests are implemented, this lesson is the target
contract—not a claim of autonomous repair capability.

---

## 12. Practice activity

For one rendered test clip:

1. record its frame rate, frame count, file hash, context hash, and package hash;
2. assemble the visual, episode, audio, and boundary locks;
3. select five coarse review frames;
4. invent one hypothetical suspicious window and inspect it frame by frame;
5. write one structured finding with exact frame range and violated authority;
6. choose trim, regenerate, replace source, audio repair, or context revision;
7. write a Wan repair job that changes only the failing interval;
8. list the visual and audio evidence needed before the splice can be approved.

---

## 13. Completion checklist

- [ ] Qwen VL receives resolved context, approved references, hashes, and video evidence.
- [ ] Frame localization uses a coarse scan followed by dense inspection.
- [ ] Every finding names exact frames, evidence, severity, and violated authority.
- [ ] The repair changes the smallest valid story and generation unit.
- [ ] Wan receives stable boundary anchors and the same continuity locks.
- [ ] Character shape, scale, wardrobe, emotion, and movement remain continuous.
- [ ] Voice, dialogue, music, ambience, and sound effects remain version- and hash-locked.
- [ ] Qwen VL does not claim to verify audio identity from visual frames alone.
- [ ] The repaired segment is stored as a new attempt and re-reviewed.
- [ ] Qwen VL and Wan never approve their own output.

