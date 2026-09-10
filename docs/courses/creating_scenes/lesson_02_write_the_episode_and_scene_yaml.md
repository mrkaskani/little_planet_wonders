# Lesson 2: Write the Episode and Scene YAML

**Study time:** 20 minutes  
**Practice time:** 20 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- create an episode at the path LPW loads;
- select characters, emotions, intensity, and location by ID;
- describe conversation, music, ambience, sound effects, and camera intent;
- declare reference and approval requirements without authorizing production.

---

## 2. Create the episode path

Use this preferred nested layout:

```text
src/lpw/context/projects/<project-id>/episodes/<episode-id>/episode.yaml
```

For the sample project:

```text
src/lpw/context/projects/riri-yoyo/episodes/episode-001/episode.yaml
```

The folder name and top-level YAML `id` must agree. LPW also accepts a flat
`episodes/<episode-id>.yaml`, but the nested form leaves room for future scripts,
boards, cue plans, and review records associated with the episode.

---

## 3. Start with identity and authority

```yaml
id: episode-001
type: episode-context
version: 1
status: draft-example-awaiting-story-and-dialogue-approval
title: A Warm Light in the Garden

metadata:
  project_id: riri-yoyo
  audience_age: "3-6"
  language: English
  educational_focus: greeting-a-friend-and-naming-a-light

source_authority:
  characters:
    riri: ../../characters/riri/character.yaml
    yoyo: ../../characters/yoyo/character.yaml
  voices:
    riri: ../../characters/riri/voice-profile.yaml
    yoyo: ../../characters/yoyo/voice-profile.yaml
  acting_style: ../../characters/acting-style.yaml
  relationships: ../../characters/relationships.yaml
  location: ../../locations/evening_night/location.yaml
  music: ../../audios/music.yaml
  location_music: ../../locations/evening_night/music-profile.yaml
  ambience: ../../audios/ambience.yaml
  sound_effects: ../../audios/sound-effects.yaml
  mixing: ../../audios/mixing.yaml
  voice_production: ../../audios/voice-production.yaml
  s2v_input: ../../audios/s2v-input-spec.yaml
  references: ../../references.yaml
  continuity: ../../continuity/initial-state.yaml
  wan_review_cards: ../../wan22-review-cards.yaml
  auto_editing: ../../auto-editing.yaml
```

`source_authority` makes authorship and review easier to audit. The loader uses
the selected IDs to resolve characters and location; the relative paths are
documentary provenance and should still point to real files.

---

## 4. Select the default location and character states

```yaml
location_id: kindergarten-evening-night

characters:
  - id: riri
    episode_role: gentle-greeter-and-reassuring-friend
    emotion:
      id: happy
      intensity: level_2
      contract: happiness
    voice_identity:
      profile_id: riri
      voice_id: riri-v1
      identity_reference: neutral-friendly
      performance_reference: happy-gentle
      preserve_across_episode_and_repairs: true
    starting_state:
      pose: stable-full-body-standing-pose
      gaze_target: yoyo-face
      mouth: closed-or-resting-before-speech
    intention: welcome-yoyo-and-point-out-the-warm-garden-light

  - id: yoyo
    episode_role: curious-explorer-and-active-listener
    emotion:
      id: curious
      intensity: level_2
      contract: curiosity
    voice_identity:
      profile_id: yoyo
      voice_id: yoyo-v1
      identity_reference: neutral-friendly
      performance_reference: curious
      preserve_across_episode_and_repairs: true
    starting_state:
      pose: stable-full-body-standing-pose-with-small-forward-lean
      gaze_target: warm-garden-light
      beak: softly-closed-before-speech
    intention: notice-the-light-and-share-the-discovery
```

This is a selection layer. `id: riri` causes LPW to load Riri's full canonical
character YAML. `emotion.id: happy` selects Riri's full `happy` expression, and
the intensity and contract are resolved from the shared acting style.

Prefer an explicit emotion object over a bare string because it records the
performance strength and contract. LPW accepts a string, but the explicit form
is clearer for production.

---

## 5. Define the narrative boundary

```yaml
narrative:
  premise: >-
    Riri and Yoyo arrive at the familiar kindergarten garden at calm blue night
    and notice a small warm light near the entrance.
  opening_state: both-friends-stand-together-on-the-readable-garden-path
  story_beat: notice-name-and-share-one-safe-gentle-discovery
  resolution: both-friends-identify-the-light-and-feel-calm-and-welcome
  safety_boundary:
    - remain-on-the-approved-readable-path
    - entrance-and-character-faces-remain-visible
    - no-touching-hot-lamps-or-electrical-fixtures
    - no-threatening-darkness-or-startling-event
```

The narrative section explains why the scene exists. It should be short enough
that every planned action can be checked against it.

---

## 6. Add an episode-wide continuity contract

Continuity information must be available to generation, Qwen VL review,
automated editing, and Wan 2.2 repair. Add a compact contract that references
the reusable authorities and identifies the fields that no downstream tool may
silently change:

```yaml
continuity_contract:
  authority_hierarchy:
    - approved-project-and-series-context
    - approved-character-location-voice-music-and-reference-context
    - this-episode-selection
    - current-scene-shot-and-segment-state
    - previous-approved-runtime-end-state

  character_identity:
    reference_registry: ../../references.yaml
    relationship_and_scale: ../../characters/relationships.yaml
    preserve:
      - character-species-shape-and-proportions
      - face-eyes-markings-and-permanent-colors
      - material-and-wardrobe-identity
      - riri-to-yoyo-relative-scale

  voice_identity:
    riri:
      profile: ../../characters/riri/voice-profile.yaml
      profile_id: riri
      voice_id: riri-v1
    yoyo:
      profile: ../../characters/yoyo/voice-profile.yaml
      profile_id: yoyo
      voice_id: yoyo-v1
    rules:
      - emotion-may-change-performance-but-never-speaker-identity
      - every-final-dialogue-line-requires-exact-transcript-and-audio-hash
      - picture-only-repair-reuses-the-approved-dialogue-stem

  music_identity:
    project_profile: ../../audios/music.yaml
    location_profile: ../../locations/evening_night/music-profile.yaml
    scene_state_id: evening-night-friendship
    exact_render_path: null
    exact_render_sha256: null
    lock_status: pending-approved-render
    rules:
      - preserve-recurring-motif-language-across-episodes
      - preserve-the-exact-approved-stem-and-offset-during-picture-repair
      - intentional-music-change-requires-a-new-version-and-review

  runtime_boundaries:
    require_previous_approved_end_frame: true
    require_approved_start_frame: true
    require_expected_end_state: true
    never-reset-state-without-a-scripted-transition: true

  qwen_vl_review:
    locate_first_and_last_bad_frame: true
    cite_violated_authority_and-rule: true
    visual_review_does_not_claim_voice-or-music-identity-pass: true

  wan_repair:
    smallest-valid-bounded-segment: required
    create-new-immutable-attempt: true
    overwrite-source-attempt: false
    require-qwen-vl-recheck-audio-continuity-check-and-human-approval: true
```

Across episodes, preserve the same permanent character shape, proportions,
voice identity, and recurring musical language. Inside a scene or repair, also
preserve the exact approved voice and music files by hash. An intentional new
wardrobe, location state, emotional performance, or cue is allowed only when the
episode declares the change and creates new reviewed runtime evidence.

---

## 7. Add one complete scene

```yaml
scenes:
  - id: moonlit-garden-greeting
    order: 1
    title: The Warm Garden Light
    location_id: kindergarten-evening-night
    time_of_day: night
    duration_target_seconds: 12

    visual_prompt_intent: >-
      Riri and Yoyo stand together on the clearly lit kindergarten garden path
      at calm blue night, looking toward one localized warm entrance light.
      Preserve the approved building, entrance, path, tree groups, and practical
      light positions.

    character_states:
      riri:
        emotion: happy
        intensity: level_2
        action: turns-gaze-to-the-light-with-one-small-paw-lift
      yoyo:
        emotion: curious
        intensity: level_2
        action: follows-riris-gaze-with-one-clear-head-tilt

    conversation:
      language: English
      overlap: forbidden
      lines:
        - order: 1
          speaker: riri
          emotion: happy
          text: "Hi, Yoyo! Look at the warm light."
          listener: yoyo
          listener_state: attentive-closed-beak-and-gaze-on-the-light
        - order: 2
          speaker: yoyo
          emotion: curious
          text: "Is that our garden light?"
          listener: riri
          listener_state: warm-attentive-closed-mouth-and-small-head-tilt
        - order: 3
          speaker: riri
          emotion: affectionate
          text: "Yes. It helps us see the path."
          listener: yoyo
          listener_state: happy-understanding-and-stable-closed-beak
```

Dialogue text is exact production intent. Keep the non-speaker's mouth or beak
closed and give the listener a readable behavior. `overlap: forbidden` prevents
ambiguous turn-taking and simplifies voice and lip-sync production.

---

## 8. Add the audio, camera, and generation intent

Continue inside the same scene item:

```yaml
    music:
      authority: ../../audios/music.yaml
      location_profile: ../../locations/evening_night/music-profile.yaml
      profile: soft-kids-pop
      theme: friendship
      state_id: evening-night-friendship
      activity: talking
      intensity: low
      dialogue_ducking_required: true
      vocals: forbidden

    ambience:
      authority: ../../audios/ambience.yaml
      location_profile: kindergarten_exterior_garden
      state: calm-night
      continuity: preserve-across-the-scene
      level: soft-below-dialogue

    sound_effects:
      authority: ../../audios/sound-effects.yaml
      cues:
        - id: riri-small-paw-step
          source: visible-riri-step
          scale: tiny
          priority: low
        - id: yoyo-soft-head-tilt-feather-rustle
          source: visible-yoyo-head-tilt
          scale: tiny
          priority: low
      dialogue_priority: absolute
      unmotivated_effects: forbidden

    camera:
      framing: medium-wide-full-character-readable
      angle: preschool-eye-level
      movement: slow-gentle-push-in
      composition: characters-path-warm-entry-light

    generation:
      target_mode: s2v
      reference_requirement: approved-single-frame-character-location-composite
      board_or_collage_conditioning: forbidden
      exact_character_count: 2
      production_authorized: false
```

Use only sound effects tied to visible actions. Music and ambience stay below
dialogue. One gentle camera behavior is enough for this scene.

---

## 9. Declare the reference and approval gates

```yaml
reference_plan:
  character_identity_sources:
    - riri-neutral-full-body-v001
    - yoyo-neutral-full-body-v001
  location_identity_source: kindergarten-evening-night-primary-master-v001
  required_new_reference: episode-001-moonlit-garden-greeting-s2v-start-frame-v001
  required_properties:
    - one-coherent-single-frame-image
    - exact-two-approved-characters
    - approved-v1-location-geometry
    - episode-emotions-visible-and-within-level-2
    - speaker-and-listener-mouth-or-beak-start-at-rest
    - eyes-gaze-ground-contact-and-movement-space-readable
    - no-text-label-watermark-or-duplicate-character
  approval_status: missing-awaiting-generation-and-human-review

approval_boundary:
  example_schema_approved: false
  story_and_dialogue_approved: false
  character_emotions_resolve_from_yaml: required
  location_identity_approved_for-example: true-v1-only
  s2v_start_frame_approved: false
  production_authorized: false
```

Keep all approval flags false while the scene is a draft. Successful YAML
loading, prompt compilation, or image generation is not human approval.

---

## 10. Common mistakes

- Copying full character definitions into every episode.
- Writing an emotion that is absent from a character's expression library.
- Selecting a location by folder name rather than its YAML `id`.
- Mixing several actions and camera movements into one generation unit.
- Adding sound effects that have no visible or environmental source.
- Using a contact sheet or reference board directly as the final S2V frame.
- Setting `production_authorized: true` before review.
- Putting an API key in YAML.
- Letting a visual repair silently change voice, music, ambience, or an episode-
  persistent character state.

---

## 11. Practice activity

Create `episode.yaml` for one new draft episode. Include at least:

- one approved location;
- one or two known characters;
- one valid emotion and intensity per character;
- one scene with a clear beginning and ending state;
- exact conversation lines or an explicit `conversation: none`;
- music, ambience, and motivated sound-effect intent;
- one camera behavior;
- an episode-wide continuity contract for character shape, voice, music,
  location, and runtime boundaries;
- a required new reference frame;
- approval flags set to false.

Compare your structure with the complete
[`episode-001` example](../../../src/lpw/context/projects/riri-yoyo/episodes/episode-001/episode.yaml).

---

## 12. Completion checklist

- [ ] My episode path and YAML ID agree.
- [ ] My episode selects existing IDs instead of duplicating authorities.
- [ ] Every scene names its location, characters, action, and duration target.
- [ ] Dialogue contains speaker, listener, emotion, exact text, and listener state.
- [ ] Music, ambience, and effects protect dialogue clarity.
- [ ] The camera has one readable framing and movement plan.
- [ ] Reference requirements are explicit.
- [ ] Character shape, scale, voice identity, and music identity have reusable authorities.
- [ ] Approved dialogue and music renders will be locked by path, hash, and timeline position.
- [ ] Qwen VL and Wan repair rules inherit the same context and continuity boundaries.
- [ ] Every production and approval gate remains false for the draft.
