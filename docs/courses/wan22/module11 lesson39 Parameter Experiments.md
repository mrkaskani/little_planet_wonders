# Module 11

## Lesson 39 of 40 — Parameter Experiments

**Study time:** approximately 30 minutes  
**Practice time:** approximately 30 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- design controlled Wan experiments;
- establish a baseline generation;
- change one variable at a time;
- evaluate seed, step count, guidance, prompt, resolution, frame count, solver, shift, and source image;
- distinguish causal evidence from coincidence;
- build an experiment matrix and technical report;
- stop testing when improvements no longer justify cost.

---

## 2. Why experiments need structure

Video generation contains many variables.

A result can change because of:

- random seed;
- prompt wording;
- source image;
- audio;
- pose guidance;
- resolution;
- frame count;
- sampling steps;
- solver;
- guidance strength;
- sampling shift;
- model choice.

Changing several together produces an output, but not knowledge.

A controlled experiment produces evidence about one variable’s effect.

---

## 3. Baseline

A **baseline** is the reference configuration used for comparison.

Record:

```text
Model:
Workflow:
Prompt:
Source image:
Audio:
Pose guidance:
Seed:
Resolution:
Frame count:
FPS:
Sampling steps:
Solver:
Guidance:
Shift:
Generation time:
```

Without a recorded baseline, later comparisons become unreliable.

---

## 4. One-variable-at-a-time method

Example:

| Run | Changed variable | Purpose |
|---|---|---|
| 1 | None | Baseline |
| 2 | More steps | Compare refinement |
| 3 | Higher guidance | Compare prompt adherence |
| 4 | Different seed | Compare composition |

All other relevant settings remain fixed.

This method is sometimes called OFAT: one factor at a time.

---

## 5. Seed experiment

Changing seed tests variation in the random starting state.

Observe:

- composition;
- subject design;
- camera framing;
- movement path;
- object placement;
- success rate.

Do not conclude that one seed number is universally “good.” A seed is meaningful only with the complete configuration.

Useful report:

```text
Five seeds tested.
Three preserved one subject.
Two produced background drift.
Seed 104 had the strongest motion but weaker hand detail.
```

---

## 6. Sampling-step experiment

Purpose:

- test refinement versus cost.

Observe:

- detail;
- prompt adherence;
- motion smoothness;
- temporal stability;
- generation time;
- diminishing returns.

Possible pattern:

```text
low steps → unfinished
medium steps → major improvement
high steps → small improvement at much higher cost
```

More steps do not guarantee correction of wrong composition.

---

## 7. Guidance-strength experiment

Guidance controls how strongly the generated trajectory follows conditions.

Lower guidance may provide:

- more natural freedom;
- weaker prompt adherence;
- less forced appearance.

Higher guidance may provide:

- stronger semantic adherence;
- more rigid or exaggerated output;
- possible artifacts if excessive.

Review both compliance and visual naturalness.

---

## 8. Prompt-wording experiment

Prompt tests should change one semantic component.

Example baseline:

```text
The character raises her hand.
```

Controlled alternatives:

- “slowly raises her right hand”;
- “raises her right hand to shoulder height”;
- “raises her right hand while her torso remains still.”

Do not simultaneously change character, environment, camera, and motion wording.

Evaluate whether added detail resolves ambiguity or creates conflicts.

---

## 9. Resolution experiment

Changing resolution tests spatial detail and cost.

Observe:

- facial detail;
- hair;
- hands;
- small objects;
- background texture;
- memory;
- generation time.

Do not expect resolution to repair:

- wrong subject count;
- wrong movement direction;
- missing action;
- identity swap.

Those are structural or semantic failures.

---

## 10. Frame-count experiment

Changing frame count affects duration when FPS remains constant.

Observe:

- action pacing;
- availability of intermediate poses;
- identity drift;
- background stability;
- temporal cost;
- completeness of action.

Longer is not always better.

If a longer shot drifts, split it into shorter shots instead of continually increasing constraints.

---

## 11. Solver experiment

Change only the numerical solver while keeping step count and other settings fixed.

Observe:

- trajectory stability;
- detail;
- motion;
- artifact type;
- generation time.

A step count is not directly comparable across every solver. After initial solver comparison, test the strongest solver at several step counts.

---

## 12. Sampling-shift experiment

Sampling shift changes how generation effort is distributed along the trajectory.

At a conceptual level, it may change emphasis between:

- high-noise structural stages;
- low-noise detail stages.

Observe:

- composition;
- motion structure;
- texture;
- identity;
- fine stability.

Because its effect can interact with model and resolution, document it carefully rather than assuming one universal best value.

---

## 13. Source-image experiment

For I2V or S2V, test source-image quality while keeping the motion direction fixed.

Possible source variants:

- clearer face;
- simpler background;
- more movement space;
- different framing;
- corrected anatomy;
- simplified clothing pattern.

Review whether the source improvement reduces drift or motion failure.

This experiment often provides more value than endlessly rewriting the prompt.

---

## 14. Experiment hierarchy

Test in this order:

1. workflow and model choice;
2. source quality;
3. prompt clarity;
4. seed;
5. duration and framing;
6. sampling configuration;
7. final resolution.

Why this order?

Structural decisions have larger impact than final-detail settings.

Do not optimize texture before confirming that the shot contains the correct subject and action.

---

## 15. Evaluation rubric

Use consistent categories.

| Category | Questions |
|---|---|
| Semantic correctness | Are subject, action, environment, and objects correct? |
| Composition | Is framing and placement correct? |
| Motion | Is movement natural and complete? |
| Identity | Does the subject remain stable? |
| Temporal stability | Do background, objects, and textures remain stable? |
| Detail | Are face, hands, and textures acceptable? |
| Audio sync | Does visible performance align with speech? |
| Efficiency | Was the result worth its time and memory cost? |

---

## 16. Experiment matrix

| Run | Variable | Value | Result summary | Score | Next action |
|---:|---|---|---|---:|---|
| 1 | Baseline | — | Correct composition, weak hand | 3.4 | Test slower motion |
| 2 | Prompt | Slower hand raise | Better hand, same face | 4.0 | Keep prompt |
| 3 | Seed | New seed | Better face, wrong background | 3.2 | Reject seed |
| 4 | Steps | Higher | Slight detail gain | 4.1 | Cost not justified |

The matrix should lead to a decision, not simply collect outputs.

---

## 17. Reproducibility package

Store together:

- prompt file;
- source image version;
- audio version;
- pose version;
- complete settings;
- output video;
- review score;
- notes;
- selected/rejected status.

Use clear names such as:

```text
shot_04_i2v_prompt_v03_seed_104_take_02
```

The purpose is to reconnect every output with the conditions that created it.

---

## 18. When to stop experimenting

Stop when:

- the shot meets acceptance criteria;
- additional steps show diminishing returns;
- remaining defects require shot redesign;
- the model cannot satisfy the constraint reliably;
- a simpler workflow or edit solves the problem;
- cost exceeds production value.

Do not continue random regeneration without a new hypothesis.

---

## 19. Practical experiment assignment

Choose one I2V shot.

Baseline:

```text
One character slowly reaches toward a red cup.
Her torso and feet remain still. Fixed camera.
```

Run these tests:

1. baseline;
2. slower movement wording;
3. different seed;
4. shorter frame count;
5. higher step count;
6. improved source image.

Change only one variable per run.

Complete the experiment matrix and select the strongest next action.

---

## 20. Expected result

You should be able to say not only which output looks best, but why.

Example conclusion:

```text
The improved source image produced the largest gain because the original hand was partially hidden. Higher sampling steps improved texture but did not repair the hand trajectory. The shorter shot reduced face drift. The production version should use source image B, prompt version 2, the original solver, and the shorter duration.
```

---

## 21. Failure analysis

### Failure: all variables changed

No causal conclusion is possible.

### Failure: only one output reviewed

You cannot compare quality or reliability.

### Failure: no baseline saved

Later improvements cannot be measured.

### Failure: best frame chosen, motion ignored

Video quality requires temporal review.

### Failure: endless seed search

If every seed fails similarly, redesign the prompt, source, or shot.

### Failure: higher cost accepted for invisible improvement

Use measurable acceptance criteria and stop at diminishing returns.

---

## 22. Plain-language explanation

A controlled experiment is like changing one ingredient in a recipe. If you change the oven temperature, flour, sugar, and cooking time together, you cannot know what improved the cake.

Video generation is the same. Change one variable, compare against a baseline, and write down what happened.

---

## 23. Important terminology

| Term | Meaning |
|---|---|
| Baseline | Reference configuration |
| Independent variable | Setting intentionally changed |
| Controlled variable | Setting intentionally kept constant |
| Confounding variable | Uncontrolled change that obscures cause |
| Hypothesis | Predicted effect of a change |
| Acceptance criteria | Conditions defining a usable result |
| Diminishing returns | Increasing cost with decreasing improvement |
| Reproducibility | Ability to repeat a documented setup |
| Experiment matrix | Table recording runs and results |

---

## 24. Short quiz

1. What is a baseline?
2. Why change one variable at a time?
3. What does a seed experiment primarily test?
4. Can more steps fix every composition error?
5. What should a resolution experiment evaluate?
6. Why is source-image testing important?
7. What is diminishing returns?
8. When should random regeneration stop?

---

## 25. Quiz answers

1. The recorded reference setup used for comparison.
2. To attribute changes to a likely cause.
3. Variation caused by different random starting states.
4. No.
5. Spatial detail, memory, time, and whether added resolution benefits the shot.
6. Many I2V failures begin with poor anatomy, framing, or movement space.
7. Each additional cost produces less improvement.
8. When there is no new hypothesis, acceptance is met, or the shot needs redesign.

---

## 26. Completion checklist

- [ ] I can build a baseline.
- [ ] I can change one variable at a time.
- [ ] I can test all major generation variables.
- [ ] I can score video across consistent categories.
- [ ] I can build an experiment matrix.
- [ ] I can write an evidence-based conclusion.
- [ ] I can recognize diminishing returns.
- [ ] I know when to redesign instead of regenerate.
