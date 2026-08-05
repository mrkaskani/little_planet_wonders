# Module 7

## Lesson 26 of 40 — T2V Generation and Evaluation

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Generate and compare multiple T2V candidates systematically.
- Evaluate semantic correctness, subject count, motion, camera, consistency, background, and aesthetics.
- Separate technical acceptance from personal preference.
- Use seeds as a controlled variation tool.
- Select candidates using a repeatable scorecard.
- Decide whether to accept, regenerate, simplify, or replace a shot.

---

## 2. Why one generation is not enough

T2V begins from a random latent state.

The same prompt can produce multiple valid or invalid interpretations.

A single result may be:

- Structurally wrong
- Correct but visually weak
- Beautiful but inconsistent
- Technically strong but unsuitable for the story

Production therefore requires candidate comparison.

---

## 3. Controlled seed experiment

Use the same:

- Model
- Prompt
- Resolution
- Frame count
- Sampling steps
- Solver
- Guidance
- Shift

Change only the seed.

This reveals how the random starting state influences:

- Composition
- Character design
- Motion
- Camera
- Background

---

## 4. Candidate table

| Candidate | Seed | Structural result | Motion result | Decision |
|---|---:|---|---|---|
| A | 10 | Correct | Weak | Regenerate or revise |
| B | 20 | Wrong count | Smooth | Reject |
| C | 30 | Correct | Strong | Shortlist |
| D | 40 | Correct | Strong but drifting | Repair or reject |

Do not choose only by the most attractive still frame.

---

## 5. Evaluation category 1 — Semantic correctness

Semantic correctness asks whether the video matches the intended meaning.

Review:

- Correct subject
- Correct action
- Correct environment
- Correct object relationships
- Correct visual style
- Correct emotional meaning

Example:

Prompt requests a fox pausing beside a watering can.

A fox walking past the watering can without pausing is semantically incomplete.

---

## 6. Evaluation category 2 — Character count

Count every important subject.

Reject or flag:

- Extra characters
- Missing characters
- Character duplication
- Character merging
- Subject switching

Count errors are broad structural failures.

Fine detail cannot compensate for incorrect subject count.

---

## 7. Evaluation category 3 — Motion quality

Review:

- Action begins clearly
- Intermediate poses are believable
- Movement speed is appropriate
- No teleportation
- No sliding
- No repeated or reversed movement
- Action completes or reaches the intended endpoint

Motion should be reviewed at normal speed and frame by frame.

---

## 8. Evaluation category 4 — Camera movement

Check whether the camera follows the prompt.

Review:

- Fixed camera remains fixed
- Push-in is smooth
- Pan direction is correct
- Camera does not suddenly rotate
- Subject remains framed
- Horizon and geometry remain stable

Unrequested camera motion can hide or amplify character problems.

---

## 9. Evaluation category 5 — Temporal consistency

Review stability across time:

- Face
- Hair
- Clothing
- Body proportions
- Object shape
- Object color
- Background geometry
- Lighting direction

Temporal consistency is about preserving identity while allowing intended motion.

---

## 10. Evaluation category 6 — Background stability

Background review should include:

- Walls, paths, trees, and furniture remain positioned correctly
- No object duplication
- No sudden scene changes
- No texture boiling
- No horizon movement when the camera is fixed

A complex background may look impressive in one frame but unstable over time.

---

## 11. Evaluation category 7 — Aesthetic quality

Aesthetic review includes:

- Composition
- Color harmony
- Lighting
- Visual clarity
- Style quality
- Emotional appeal
- Production suitability

Aesthetic quality is important only after minimum technical correctness is met.

---

## 12. Acceptance gates

A candidate can pass through three gates.

### Gate 1 — Structural acceptance

- Correct subjects
- Correct major objects
- Correct composition
- Correct action direction

### Gate 2 — Temporal acceptance

- Usable motion
- Stable identity
- Stable background
- Correct camera

### Gate 3 — Visual acceptance

- Good detail
- Good lighting
- Good style
- Suitable for editing

Failure at an earlier gate usually makes later beauty irrelevant.

---

## 13. Scorecard

Use a five-point score for each category:

| Score | Meaning |
|---:|---|
| 1 | Unusable |
| 2 | Major problems |
| 3 | Usable with compromise |
| 4 | Strong |
| 5 | Production-ready |

Example categories:

- Semantic correctness
- Subject count
- Motion
- Camera
- Identity stability
- Background stability
- Detail
- Aesthetics

---

## 14. Weighted evaluation

Some categories matter more for certain shots.

### Establishing shot

Prioritize:

- Environment
- Composition
- Camera
- Background stability

### Character action shot

Prioritize:

- Identity
- Anatomy
- Motion
- Object interaction

### Transition shot

Prioritize:

- Camera movement
- Visual continuity
- Edit compatibility

Use weights based on shot purpose.

---

## 15. Technical versus creative rejection

### Technical rejection

- Extra limb
- Identity drift
- Background warping
- Wrong action
- Severe flicker

### Creative rejection

- Mood is wrong
- Composition does not fit the sequence
- Performance lacks emotion
- Color conflicts with surrounding shots

Record both types separately.

---

## 16. Accept, regenerate, or redesign

### Accept

Use when the candidate meets technical and creative requirements.

### Regenerate

Use when the shot design is sound but the random outcome is weak.

### Revise prompt

Use when the same misunderstanding appears across several seeds.

### Redesign shot

Use when the action is too complex or the workflow is unsuitable.

### Replace with I2V

Use when exact character or composition control becomes important.

---

## 17. Change one variable at a time

If several seeds all fail for the same reason, change one prompt element.

Example:

```text
Original:
The fox walks through the garden and pauses beside the watering can.

Revision:
One fox walks slowly from left to right and stops beside one blue watering can.
```

Keep model and sampling settings fixed while testing the wording revision.

---

## 18. Review at multiple speeds

### Normal playback

Reveals:

- Overall motion
- Pacing
- Emotional effect
- Camera behavior

### Slow playback

Reveals:

- Pose transitions
- Object deformation
- Flicker
- Identity drift

### Frame-by-frame

Reveals:

- Extra limbs
- Hand transitions
- Small temporal discontinuities
- Exact failure point

---

## 19. Contact-sheet review

Extract representative frames conceptually from:

- Start
- Early motion
- Middle
- Late motion
- End

A frame sequence helps detect gradual changes in:

- Face
- Clothing
- Object shape
- Background
- Camera

A contact sheet should supplement, not replace, motion playback.

---

## 20. Generation log

Record:

- Candidate ID
- Seed
- Prompt version
- Settings
- Scores
- Failure notes
- Decision
- Next action

Example next actions:

- Try another seed
- Simplify action
- Fix camera
- Reduce background complexity
- Move to I2V

---

## 21. Plain-language explanation

Generating candidates is like filming several takes.

One take may have the best acting but poor framing.

Another may look beautiful but miss the action.

The director compares them against the shot’s purpose rather than selecting the most attractive single frame.

---

## 22. Important terminology

| Term | Meaning |
|---|---|
| Candidate | One generated take |
| Semantic correctness | Match between output and intended meaning |
| Structural acceptance | Correct subjects, objects, composition, and action plan |
| Temporal consistency | Stability across time |
| Aesthetic quality | Visual appeal and style suitability |
| Acceptance gate | Required quality stage before approval |
| Scorecard | Standard evaluation form |
| Weighted score | Score adjusted by shot importance |
| Regeneration | Creating another candidate |
| Shot redesign | Changing the production plan rather than only settings |

---

## 23. Practical activity

Evaluate four hypothetical candidates for this prompt:

```text
One red fox walks slowly through a garden, stops beside one blue watering can, and looks toward the camera. Fixed medium-wide shot.
```

- Candidate A: one fox, correct motion, unstable flowers
- Candidate B: two foxes, smooth motion, beautiful lighting
- Candidate C: one fox, correct scene, never stops
- Candidate D: one fox, correct action, stable scene, slightly soft fur

Choose the best candidate and explain the decision.

---

## 24. Expected result

Candidate D is usually the strongest production choice because:

- Subject count is correct
- Action is correct
- Scene is stable
- The remaining issue is local softness

Candidate B should be rejected despite strong aesthetics because subject count is incorrect.

Candidate A may be usable only if the background instability is minor and repairable.

Candidate C fails the required action.

---

## 25. Failure analysis

### Failure 1 — Beautiful still frame selected, motion ignored

**Result:** The edited clip contains severe drift or deformation.

### Failure 2 — Seeds changed together with prompt and solver

**Result:** Candidate comparison is not controlled.

### Failure 3 — Every weak result is regenerated without diagnosis

**Result:** Repeated cost without learning.

### Failure 4 — Same structural failure across many seeds

**Likely cause:** Prompt or shot-design problem rather than seed alone.

### Failure 5 — Slight texture issue causes rejection of otherwise strong result

**Risk:** Production wastes a usable candidate while prioritizing minor detail over structure.

---

## 26. Short quiz

1. Why should several seeds be tested?
2. What is semantic correctness?
3. Why should subject count be checked before texture?
4. Name three motion-quality checks.
5. What is an acceptance gate?
6. When should the prompt be revised instead of only changing the seed?
7. When should T2V be replaced with I2V?
8. Why review at normal and slow speeds?

---

## 27. Quiz answers

1. Seeds produce different compositions and motion from the same prompt.
2. Whether the output matches the intended meaning.
3. Subject count is a global structural requirement; texture cannot repair it.
4. Any three of: correct order, smooth path, no sliding, no teleportation, appropriate speed, completed action.
5. A required quality level that must be passed before later evaluation.
6. When the same misunderstanding repeats across several seeds.
7. When exact identity or composition control becomes important.
8. Normal speed reveals overall performance; slow review reveals temporal defects.

---

## 28. Completion checklist

- [ ] I can run a controlled seed comparison.
- [ ] I can evaluate semantic correctness and subject count.
- [ ] I can evaluate motion and camera behavior.
- [ ] I can identify temporal and background instability.
- [ ] I can separate technical and creative rejection.
- [ ] I can use an acceptance-gate scorecard.
- [ ] I know when to regenerate, revise, redesign, or change workflow.
- [ ] I can document candidate decisions reproducibly.
