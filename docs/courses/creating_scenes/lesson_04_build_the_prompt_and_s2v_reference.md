# Lesson 4: Build the Prompt and S2V Reference

**Study time:** 15 minutes  
**Practice time:** 20 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- turn resolved context into one task-specific image prompt;
- select the correct character and location reference assets;
- plan a clean start frame for speech-to-video or image-conditioned video;
- register a manually created image for the S2V handoff.

---

## 2. Compile, do not concatenate

A strong creative prompt is not every YAML file pasted together. Select only the
context relevant to the current output:

```text
task and audience
+ exact character identity
+ resolved expression and intensity
+ location geometry and lighting
+ current scene state and one action
+ camera and composition
+ audio-aware mouth, gaze, and listener state
+ invariants and negative constraints
+ output and review requirements
```

Repeated or irrelevant detail weakens priority. Contradictory detail makes the
generation impossible to review.

---

## 3. Use a prompt package

Before sending anything to a provider, build a structured package like this:

```yaml
prompt_package:
  project_id: riri-yoyo
  episode_id: episode-001
  scene_id: moonlit-garden-greeting
  context_hash: <resolved-context-hash>
  output_type: s2v-start-frame

  task: >-
    Create one clean, coherent start frame for the moonlit garden greeting.

  character_direction:
    riri:
      identity_source: riri-neutral-full-body-v001
      emotion: happy
      intensity: level_2
      pose: stable standing pose with one small paw lift
      gaze: warm entrance light
      mouth: resting and closed before speech
    yoyo:
      identity_source: yoyo-neutral-full-body-v001
      emotion: curious
      intensity: level_2
      pose: stable standing pose with one gentle head tilt
      gaze: warm entrance light
      beak: softly closed before speech

  location_direction:
    identity_source: kindergarten-evening-night-primary-master-v001
    preserve:
      - approved-v1-building-and-entrance-geometry
      - readable-path
      - tree-group-placement
      - localized-warm-practical-light
      - calm-blue-night-separation

  camera:
    framing: medium-wide-full-character-readable
    angle: preschool-eye-level
    movement_space: allow-slow-gentle-push-in

  invariants:
    - exact-two-characters
    - one-coherent-scene
    - correct-character-scale-and-ground-contact
    - faces-eyes-and-path-readable
    - no-identity-or-wardrobe-drift
    - no-location-geometry-drift

  negative_constraints:
    - no-reference-board-or-collage-layout
    - no-extra-character-or-duplicate-character
    - no-text-label-caption-logo-or-watermark
    - no-open-mouth-speaking-pose-in-the-start-frame
    - no-threatening-darkness-or-high-contrast-horror-lighting
    - no-contact-with-hot-or-electrical-fixtures

  approval_required: true
  production_authorized: false
```

This package is the creative brief for the project owner's manual image work. It
is not currently produced automatically by LPW.

---

## 4. Write the final natural-language image prompt

The structured package can produce a concise creation prompt:

> Create one clean cinematic start frame for a gentle preschool scene. Show
> exactly Riri and Yoyo together on the approved kindergarten evening-night
> garden path. Preserve their canonical identity, proportions, materials, and
> wardrobe. Riri shows her resolved happy expression at level 2, standing
> securely with one small paw lifted, eyes toward the warm entrance light, and
> mouth resting closed before speech. Yoyo shows his resolved curious expression
> at level 2, standing securely with one gentle head tilt, eyes on the same
> light, and beak softly closed. Preserve the approved V1 building, entrance,
> path, tree groups, blue night ambience, and localized warm practical light.
> Use an uncluttered eye-level medium-wide composition with both full characters,
> faces, ground contact, path, and movement space clearly readable. Output one
> coherent scene image, not a board or collage. Do not add text, labels,
> watermarks, props, duplicate characters, extra characters, altered wardrobe,
> frightening darkness, or unapproved geometry.

When preparing the manual brief, insert exact visual cues from each resolved
expression instead of relying only on the abstract words `happy` and `curious`.

---

## 5. Use references by role

Different references solve different problems:

| Reference | Purpose | Direct final S2V input? |
|---|---|---|
| Character model sheet | Identity, proportions, materials | No |
| Expression sheet | Face and emotion details | No |
| Location reference board | Geometry, palette, landmarks | No |
| Approved location master | Background identity | Source for composition |
| Clean character-location composite | Exact scene starting state | Yes, after approval |

A board or collage may help an image model understand ingredients, but it is not
a valid final S2V start frame. S2V needs one coherent image that already shows
the exact character count, positions, expressions, location, lighting, camera,
and starting state.

---

## 6. Prepare the manual image handoff safely

The project owner should:

1. receive the resolved context and context hash;
2. use only declared reference-image paths;
3. verify that every source reference exists and has an allowed status;
4. compile and follow the prompt package;
5. create one coherent candidate image manually;
6. copy the selected candidate into the declared handoff location;
7. record its creator, creation method, date, source references, and SHA-256;
8. preserve replaced candidates as immutable attempts when appropriate;
9. leave all approval fields false until human review;
10. register only the approved image as the first S2V segment's input.

The project files must record the image's identity and provenance without
embedding unrelated credentials or private creation data.

---

## 7. Current limitation

The repository resolves episode, character, emotion, acting, and location
context. It does not create the image automatically. Treat the prompt package as
a reviewed design contract and the supplied image as an unapproved candidate
until its handoff manifest and human review are complete.

---

## 8. Practice activity

Using the resolved output from Lesson 3:

1. copy the current context hash into a prompt-package draft;
2. extract the identity features needed for this framing;
3. extract each resolved expression's exact visual cues;
4. extract stable location geometry and lighting;
5. add one action-ready pose for each character;
6. add mouth, beak, eye, gaze, and listener-state rules;
7. list invariant and forbidden changes;
8. name one required clean output frame;
9. keep approval and production authorization false.

---

## 9. Completion checklist

- [ ] The prompt package records project, episode, scene, and context hash.
- [ ] Character direction comes from resolved identity and emotion context.
- [ ] Location direction names the intended approved version.
- [ ] The prompt describes one starting state and one future action.
- [ ] Mouth, beak, gaze, and listener state agree with the dialogue plan.
- [ ] Existing boards are used as source references, not final S2V frames.
- [ ] The requested output is one clean coherent scene image.
- [ ] No secret or unrelated private creation data is stored in YAML or Git.
- [ ] I have not confused local context resolution with manual image approval.
