# Module 9

## Lesson 34 of 40 — TI2V versus A14B Comparison

**Study time:** approximately 25 minutes  
**Practice time:** approximately 25 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- compare TI2V-5B with T2V-A14B and I2V-A14B by production role;
- distinguish drafting quality from final production quality;
- design a fair model comparison;
- evaluate memory, speed, detail, motion, identity, and stability;
- avoid invalid conclusions caused by changing multiple settings;
- write a model-selection recommendation supported by evidence.

---

## 2. Comparison summary from the course

| Question | TI2V-5B | A14B family |
|---|---|---|
| Faster drafting | Better suited | Slower |
| Lower memory requirement | Better suited | Higher requirement |
| One model for T2V and I2V | Yes | No; dedicated models |
| Highest-detail production | Usually weaker | Usually stronger |
| Rapid prompt testing | Strong use case | More expensive |

This table describes production suitability, not an absolute guarantee for every shot.

---

## 3. Models being compared

### TI2V-5B

- dense model;
- text-only and image-conditioned modes;
- high-compression VAE;
- efficient drafting role.

### T2V-A14B

- dedicated text-to-video model;
- A14B MoE family in the course;
- used when generating a new scene from text;
- stronger candidate for high-detail text-driven production.

### I2V-A14B

- dedicated image-to-video model;
- A14B MoE family;
- used when animating an approved image;
- stronger candidate for image-driven production quality.

The correct A14B comparison depends on whether the shot is text-driven or image-driven.

---

## 4. Why a fair comparison is difficult

A model comparison becomes invalid when several variables change together.

Examples of confounding changes:

- different prompt wording;
- different source image;
- different seed;
- different duration;
- different resolution;
- different frame count;
- different solver;
- different guidance;
- different output review criteria.

A fair comparison keeps the creative task and as many settings as possible equivalent.

---

## 5. Comparison dimensions

Evaluate models across several dimensions rather than choosing one vague “best quality” score.

### 5.1 Semantic correctness

- correct subject count;
- correct action;
- correct environment;
- correct object relationships.

### 5.2 Composition

- framing;
- subject placement;
- movement space;
- background layout;
- camera angle.

### 5.3 Motion

- natural intermediate poses;
- movement direction;
- speed;
- contact;
- stopping;
- absence of sliding.

### 5.4 Identity

- face stability;
- hair;
- clothing;
- body proportions;
- source-image preservation.

### 5.5 Detail

- face;
- hands;
- texture;
- small objects;
- background refinement.

### 5.6 Temporal stability

- flicker;
- object permanence;
- background stability;
- camera stability;
- color stability.

### 5.7 Efficiency

- generation time;
- memory demand;
- number of failed iterations;
- cost of testing seeds;
- time to an acceptable result.

---

## 6. Time-to-acceptable-result

A larger model may produce stronger individual quality, but the production metric should also consider how many experiments are affordable.

Example:

```text
TI2V:
8 quick drafts → 2 strong candidates

A14B:
2 expensive drafts → 1 strong candidate
```

The best workflow may be:

```text
many TI2V experiments
→ select prompt, seed, source, and motion
→ fewer A14B production attempts
```

This combines exploration efficiency with production quality.

---

## 7. Text-driven comparison design

Shot:

```text
One small red fox walks along a garden path and pauses beside a blue watering can. Fixed camera, soft morning light.
```

Compare:

- TI2V-5B in text mode;
- T2V-A14B.

Keep constant where supported:

- prompt;
- target duration;
- aspect ratio;
- resolution;
- evaluation rubric;
- seed strategy.

Review:

- fox count and appearance;
- garden composition;
- walking motion;
- pause timing;
- watering-can stability;
- texture;
- generation time.

---

## 8. Image-driven comparison design

Use one approved source image.

Motion:

```text
The character slowly turns toward the red book and reaches for it.
Her feet remain still. The camera remains locked.
```

Compare:

- TI2V-5B in image mode;
- I2V-A14B.

Review:

- identity preservation;
- source-image fidelity;
- hand motion;
- book permanence;
- background stability;
- fine facial detail;
- cost.

---

## 9. What TI2V may win

TI2V may be preferable when:

- many prompts must be tested;
- many seeds must be compared;
- computational resources are limited;
- the team is still planning composition;
- movement wording is not yet approved;
- final detail is not yet required;
- one model for both text and image tests simplifies workflow.

A draft is successful if it provides clear decision-making information.

---

## 10. What A14B may win

A14B may be preferable when:

- the creative setup is already approved;
- maximum available detail matters;
- final facial or texture quality is important;
- complex motion requires more capacity;
- the shot is intended for final editing;
- additional memory and generation time are acceptable.

A14B should not be used merely because it is larger. It should be used when the shot’s approved requirements justify the extra cost.

---

## 11. Seed strategy for comparison

There are two useful seed strategies.

### Same-seed comparison

Purpose:

- reduce variation in starting randomness;
- compare model behavior under a related starting condition.

Limitation:

- different architectures may interpret the seed differently;
- same number does not guarantee equivalent composition.

### Multi-seed comparison

Purpose:

- compare model reliability across several attempts;
- measure success rate rather than one lucky result.

A strong report includes both best-case quality and consistency across seeds.

---

## 12. Scoring rubric

Use a 1–5 score for each category.

| Category | Weight | TI2V score | A14B score |
|---|---:|---:|---:|
| Semantic correctness | 20% |  |  |
| Motion | 20% |  |  |
| Identity | 15% |  |  |
| Temporal stability | 15% |  |  |
| Detail | 15% |  |  |
| Efficiency | 15% |  |  |

Adjust weights according to the shot.

For a speaking close-up, identity and temporal facial stability may receive higher weight.

For an establishing shot, composition and environment may matter more.

---

## 13. Comparison report template

```text
Shot ID:
Workflow:
Model:
Prompt version:
Source image version:
Seed:
Resolution:
Frame count:
FPS:
Sampling settings:
Generation time:

Semantic correctness:
Motion:
Identity:
Temporal stability:
Detail:
Artifacts:
Production usability:
Recommended next action:
```

A report should describe evidence, not only preference.

Weak conclusion:

```text
A14B looks better.
```

Strong conclusion:

```text
A14B preserved the face and hand structure more consistently in three of four seeds, while TI2V generated drafts approximately faster and was sufficient for selecting the motion prompt.
```

---

## 14. Expected comparison patterns

Typical but not guaranteed patterns:

### TI2V

- faster iteration;
- lower memory use;
- useful composition and prompt feedback;
- weaker fine detail;
- possibly less stable identity under complex movement.

### A14B

- slower iteration;
- higher memory requirement;
- stronger texture and detail potential;
- possibly better complex motion and identity;
- higher cost per failed attempt.

The correct production pipeline may use both.

---

## 15. Failure analysis

### Invalid comparison: different source images

You are comparing image quality, not only models.

### Invalid comparison: only best output is shown

One lucky seed does not measure reliability.

### Invalid comparison: different durations

Longer duration changes temporal difficulty.

### Wrong conclusion: TI2V loses because texture is weaker

If the purpose was prompt testing, texture may not be the deciding criterion.

### Wrong conclusion: A14B always wins because it is larger

Higher capacity does not fix ambiguous prompts, poor source images, or impossible shot design.

---

## 16. Production decision matrix

| Production state | Recommended starting point |
|---|---|
| Idea exploration | TI2V text mode |
| Motion-prompt testing | TI2V image mode |
| Low-memory environment | TI2V |
| Approved T2V final shot | T2V-A14B candidate |
| Approved I2V final shot | I2V-A14B candidate |
| Uncertain prompt | TI2V first |
| Complex final detail | Compare with A14B |
| Many seeds required | TI2V for screening |

---

## 17. Plain-language explanation

TI2V is the efficient sketching team. A14B is the larger finishing team.

You would not hire the finishing team to redraw every uncertain idea. You would first test composition, timing, and movement with the sketching team. Once the plan works, the finishing team can spend more effort on the approved version.

---

## 18. Important terminology

| Term | Meaning |
|---|---|
| Fair comparison | Test controlling important variables |
| Confounding variable | Uncontrolled change that makes conclusions unclear |
| Reliability | Frequency of acceptable results across attempts |
| Best-case quality | Quality of the strongest selected output |
| Time-to-acceptable-result | Total effort required to obtain a usable output |
| Weighted rubric | Scoring system prioritizing shot-specific requirements |
| Screening | Quickly rejecting weak prompts or seeds |
| Production candidate | Output intended for final-quality evaluation |

---

## 19. Short quiz

1. Which A14B model should be compared with TI2V text mode?
2. Which A14B model should be compared with TI2V image mode?
3. Why is one seed insufficient for reliability testing?
4. What is a confounding variable?
5. Why should efficiency be part of quality evaluation?
6. Does the same seed guarantee equivalent compositions across models?
7. When is TI2V a successful choice even if detail is weaker?
8. What is the strongest combined workflow?

---

## 20. Quiz answers

1. T2V-A14B.
2. I2V-A14B.
3. It may be unusually strong or weak and does not reveal consistency.
4. A changed variable that prevents clear attribution of the result.
5. Production must account for iteration time, memory, and failed attempts.
6. No.
7. When it efficiently answers drafting questions about prompt, composition, or motion.
8. Use TI2V for broad experimentation and A14B for approved production candidates.

---

## 21. Completion checklist

- [ ] I can select the correct A14B comparison.
- [ ] I can design a controlled test.
- [ ] I can score semantic, motion, identity, stability, detail, and efficiency.
- [ ] I understand best-case versus reliability.
- [ ] I can write an evidence-based recommendation.
- [ ] I can explain why both models may belong in one pipeline.
