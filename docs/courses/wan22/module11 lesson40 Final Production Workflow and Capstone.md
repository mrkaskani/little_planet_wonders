# Module 11

## Lesson 40 of 40 — Final Production Workflow and Capstone

**Study time:** approximately 35 minutes  
**Practice time:** multi-session capstone

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- design a complete multi-shot Wan 2.2 production;
- select T2V, I2V, TI2V, or S2V for each shot;
- organize prompts, visual inputs, audio, seeds, and settings;
- review drafts structurally and technically;
- regenerate only failed shots;
- edit selected takes into a coherent sequence;
- prepare final audio and export;
- write a technical comparison report covering all four workflows.

---

## 2. Capstone goal

Produce a short edited sequence containing:

1. a T2V establishing shot;
2. an I2V character-action shot;
3. a TI2V draft and documented comparison;
4. an S2V dialogue shot;
5. a final edited sequence with sound, dialogue, and music.

The project must demonstrate both creative production and technical reasoning.

---

## 3. Complete production pipeline

```text
Story goal
→ shot list
→ workflow selection
→ asset preparation
→ prompt design
→ draft generation
→ technical review
→ controlled regeneration
→ take selection
→ editing
→ dialogue and sound
→ music
→ final mix
→ export
→ technical report
```

Each stage has an approval checkpoint. Do not move forward with unresolved structural errors.

---

## 4. Step 1 — Define the sequence

Create a simple story that can be expressed in four to six shots.

Example:

```text
A child enters a quiet garden, notices a small red fox,
walks closer, and says, “Hello, little friend.”
The fox looks up and the scene ends calmly.
```

Keep the story suitable for the available workflows.

Avoid:

- many characters;
- long object handoffs;
- rapid camera changes;
- several actions in one shot;
- exact generated text;
- long continuous dialogue.

---

## 5. Step 2 — Create the shot list

| Shot | Purpose | Workflow | Main requirement |
|---:|---|---|---|
| 1 | Establish garden | T2V | new environment from words |
| 2 | Character sees fox | I2V | approved character identity |
| 3 | Draft alternate action | TI2V | efficient motion test |
| 4 | Character speaks | S2V | audio-driven performance |
| 5 | Reaction or ending | I2V or T2V | calm visual conclusion |

Each shot should have one main action and one primary camera behavior.

---

## 6. Step 3 — Select the workflow per shot

Use the model-selection rule:

```text
Need a new scene from words:
T2V-A14B

Need to animate an approved image:
I2V-A14B

Need efficient experimentation:
TI2V-5B

Need speech-driven performance:
S2V-14B
```

Explain the decision for every shot.

Weak reason:

```text
I used I2V because it looked good.
```

Strong reason:

```text
I used I2V because the recurring character’s black hair, blue dress, and facial identity had to match the approved design.
```

---

## 7. Step 4 — Prepare production assets

Create an organized project structure.

```text
project/
├── story/
├── shot_list/
├── prompts/
├── source_images/
├── audio/
├── pose_guidance/
├── generations/
│   ├── drafts/
│   ├── candidates/
│   └── selected/
├── edit/
├── exports/
└── reports/
```

Use versioned names so every output can be traced to its input.

---

## 8. Step 5 — Prepare character continuity

For recurring characters, document:

- face shape;
- hair color and style;
- clothing;
- main colors;
- body proportions;
- accessories;
- approved source images;
- allowed expression range;
- camera angles already validated.

Use simple, strong identity features rather than many tiny patterns.

---

## 9. Step 6 — Prepare location continuity

Document:

- layout;
- dominant colors;
- lighting direction;
- time of day;
- main props;
- camera orientation;
- background complexity;
- approved establishing image or reference.

Continuity is easier when each location has stable broad shapes and a controlled palette.

---

## 10. Step 7 — Build shot prompts

### T2V prompt structure

```text
Subject
+ appearance
+ action
+ environment
+ camera
+ lighting
+ style
+ constraints
```

### I2V prompt structure

```text
Current state
+ movement
+ emotional change
+ camera behavior
+ invariants
```

### S2V direction structure

```text
Emotional delivery
+ gesture size
+ gaze
+ body stability
+ camera
+ identity invariants
```

Every prompt should be stored with a version number.

---

## 11. Step 8 — Draft before final quality

Use lower-cost drafts to test:

- composition;
- subject count;
- action direction;
- duration;
- movement space;
- camera behavior;
- prompt clarity.

TI2V can support efficient text or image tests before larger production generations.

Do not use final resolution for every uncertain experiment.

---

## 12. Step 9 — Review from structure to detail

Review in this order:

### A. Semantic structure

- correct characters;
- correct objects;
- correct action;
- correct environment.

### B. Composition

- framing;
- camera angle;
- movement space;
- subject placement.

### C. Motion

- natural trajectory;
- correct direction;
- complete action;
- stable camera;
- object contact.

### D. Temporal consistency

- identity;
- clothing;
- background;
- object permanence;
- lighting.

### E. Fine detail

- face;
- hands;
- hair;
- texture;
- decoder artifacts.

### F. Audio alignment

- mouth timing;
- pauses;
- expression;
- gestures;
- chunk boundaries.

---

## 13. Step 10 — Classify every shot

Use one status:

- **Approved:** ready for edit.
- **Repairable:** one controlled change likely solves the problem.
- **Redesign:** prompt, image, or shot structure is wrong.
- **Rejected:** output is not useful.

Do not keep generating without classifying the failure.

---

## 14. Step 11 — Controlled regeneration

For a repairable shot:

1. identify the most important defect;
2. propose one hypothesis;
3. change one variable;
4. generate a new candidate;
5. compare with baseline;
6. record the result.

Example:

```text
Defect:
Face changes during head turn.

Hypothesis:
The rotation is too large.

Change:
Reduce turn from profile to three-quarter view.
```

---

## 15. Step 12 — Select takes

The selected take must satisfy the sequence, not only look attractive alone.

Check:

- character matches adjacent shots;
- lighting and color are compatible;
- movement direction supports the edit;
- eye line is correct;
- camera scale does not jump unintentionally;
- action begins and ends at useful edit points;
- audio timing is complete.

---

## 16. Step 13 — Edit the sequence

Arrange selected takes according to the shot list.

Review:

- pacing;
- continuity;
- action flow;
- screen direction;
- shot length;
- emotional progression;
- visual rhythm.

A technically strong clip can still fail if it does not edit cleanly with neighboring shots.

---

## 17. Step 14 — Dialogue, ambience, Foley, and effects

Audio layers may include:

- dialogue;
- room tone or outdoor ambience;
- footsteps;
- clothing movement;
- object contact;
- environmental effects;
- transitions.

Do not rely on S2V dialogue alone to create a complete sound world.

Foley should support visible action without becoming distracting.

---

## 18. Step 15 — Music

Music should support:

- emotional tone;
- pacing;
- scene transitions;
- story resolution.

It should not hide:

- dialogue;
- important Foley;
- timing problems.

Use music as a storytelling layer, not as a repair for weak visuals.

---

## 19. Step 16 — Final audio mix

Balance:

- dialogue clarity;
- ambience;
- Foley;
- sound effects;
- music.

Review on more than one playback system when possible.

Check:

- speech remains understandable;
- no clipping;
- transitions are smooth;
- silence is intentional;
- music level supports rather than covers dialogue.

---

## 20. Step 17 — Final export review

Before delivery, verify:

- resolution;
- aspect ratio;
- FPS;
- duration;
- audio synchronization;
- no missing frames;
- no black accidental frames;
- correct color and brightness;
- correct file naming;
- complete beginning and ending.

Watch the exported file from beginning to end. Do not assume the timeline preview and final export are identical.

---

## 21. Required technical report

For each shot, document:

- shot ID and purpose;
- selected model and reason;
- input conditions;
- prompt version;
- source image version;
- audio and pose inputs;
- seed;
- resolution;
- frame count;
- FPS;
- sampling steps;
- solver;
- guidance and shift;
- generation time;
- observed artifacts;
- identity consistency;
- motion consistency;
- audio synchronization;
- selected take;
- recommended improvements.

---

## 22. Capstone comparison table

| Shot | Workflow | Why selected | Strongest result | Main limitation |
|---:|---|---|---|---|
| 1 | T2V | New environment |  |  |
| 2 | I2V | Character identity |  |  |
| 3 | TI2V | Efficient draft |  |  |
| 4 | S2V | Dialogue performance |  |  |
| 5 | Selected workflow | Ending requirement |  |  |

---

## 23. Acceptance criteria

### T2V establishing shot

- environment is correct;
- no unwanted main subjects;
- camera and motion are stable;
- composition supports next shot.

### I2V character-action shot

- identity remains recognizable;
- action is complete;
- source design is preserved;
- background remains stable.

### TI2V draft

- demonstrates useful prompt or motion testing;
- includes documented comparison with A14B or production target;
- clearly explains efficiency benefit and quality trade-off.

### S2V dialogue shot

- words and duration are correct;
- mouth timing is acceptable;
- pauses are stable;
- identity and emotion remain coherent.

### Final sequence

- shots edit together;
- audio is balanced;
- story is understandable;
- technical report is complete.

---

## 24. Common capstone failures

### Failure: every shot uses the same workflow

Workflow should match the shot requirement.

### Failure: no source versioning

The team cannot reproduce the selected result.

### Failure: final edit contains identity mismatch

Individual shots were approved without cross-shot continuity review.

### Failure: audio is added at the end without planning

Dialogue duration and shot timing conflict.

### Failure: too many actions in each shot

The model skips or reorders events.

### Failure: technical report lists settings but no conclusions

The report must explain why results succeeded or failed.

### Failure: selected take has beautiful frames but unstable motion

Video must be reviewed temporally, not as isolated stills.

---

## 25. Recommended capstone schedule

### Phase 1 — Planning

- story;
- shot list;
- workflow selection;
- continuity assets.

### Phase 2 — Drafting

- TI2V and lower-cost tests;
- prompt refinement;
- source-image correction.

### Phase 3 — Production generation

- final T2V, I2V, and S2V candidates;
- controlled regeneration.

### Phase 4 — Editing and sound

- select takes;
- build sequence;
- add complete audio.

### Phase 5 — Review and report

- final technical review;
- export;
- write findings.

---

## 26. Plain-language explanation

The capstone is not a test of who can generate the most clips. It is a test of who can make good decisions.

You must choose the right model, prepare the right input, diagnose failures, regenerate carefully, and combine the selected results into one coherent sequence.

---

## 27. Important terminology

| Term | Meaning |
|---|---|
| Shot list | Ordered plan of individual camera shots |
| Workflow selection | Choosing T2V, I2V, TI2V, or S2V by requirement |
| Candidate | Generated output under review |
| Selected take | Approved clip used in the edit |
| Continuity | Consistency across shots |
| Screen direction | Direction subjects appear to move across the frame |
| Acceptance criteria | Requirements a shot must meet |
| Technical report | Evidence-based record of settings, results, and conclusions |
| Final mix | Balanced combination of all audio layers |
| Delivery export | Final file prepared for use or submission |

---

## 28. Final quiz

1. Which workflow is best for a new environment generated from words?
2. Which workflow is strongest for an approved recurring character image?
3. What is TI2V’s main capstone role?
4. Which workflow is required for speech-driven performance?
5. In what order should a clip be reviewed?
6. When should a shot be redesigned instead of regenerated?
7. Why must selected takes be reviewed next to adjacent shots?
8. What must the technical report explain beyond settings?
9. Why watch the final export completely?
10. What is the central capstone skill?

---

## 29. Quiz answers

1. T2V-A14B.
2. I2V-A14B.
3. Efficient drafting, testing, and comparison.
4. S2V-14B.
5. Structure, composition, motion, temporal consistency, fine detail, then audio alignment.
6. When the source, prompt, duration, camera plan, or action structure is fundamentally unsuitable.
7. Continuity, eye line, lighting, identity, and movement direction must match.
8. Why a model was chosen, what failed, what improved, and what should happen next.
9. Export can introduce missing frames, sync issues, format errors, or different playback behavior.
10. Making evidence-based production decisions across the complete workflow.

---

## 30. Capstone completion checklist

### Planning

- [ ] Story is simple and achievable.
- [ ] Shot list is complete.
- [ ] Each shot has one main action.
- [ ] Workflow is justified for every shot.

### Assets

- [ ] Character references are approved.
- [ ] Locations and palettes are documented.
- [ ] Audio is final and clean.
- [ ] Prompts and inputs are versioned.

### Generation

- [ ] Drafts were tested before final quality.
- [ ] Baseline settings are recorded.
- [ ] Failed shots were diagnosed.
- [ ] Regenerations changed one variable at a time.

### Review

- [ ] Semantic structure is correct.
- [ ] Motion is complete and natural.
- [ ] Identity is stable.
- [ ] Background and objects remain coherent.
- [ ] Dialogue is synchronized.

### Edit and delivery

- [ ] Selected takes match across shots.
- [ ] Dialogue, ambience, Foley, effects, and music are balanced.
- [ ] Final export has been watched completely.
- [ ] Technical report is complete.
- [ ] Improvements for a future version are documented.
