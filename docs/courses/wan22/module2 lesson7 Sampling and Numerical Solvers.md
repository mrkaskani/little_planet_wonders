# Module 2

## Lesson 7 of 40 — Sampling and Numerical Solvers

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain sampling in video generation.
- Explain why continuous flow is approximated with discrete steps.
- Understand the role of a numerical solver.
- Explain Euler-style stepping.
- Describe UniPC and DPM++ conceptually.
- Understand speed–quality trade-offs.
- Explain why more steps do not always help.
- Design controlled sampling experiments.

---

## 2. Connection to flow matching

Flow matching describes a continuous trajectory:

```text
Initial noise
→ follow predicted velocities
→ generated video
```

A real system cannot perform infinitely many tiny updates.

It approximates the path using a finite number of **sampling steps**.

---

## 3. What sampling means

Sampling means producing a new result from the trained model.

```text
Random latent state
→ update 1
→ update 2
→ update 3
→ ...
→ final latent video
```

Each update may use:

- Current latent state
- Current generation time
- Predicted velocity
- Text, image, or audio conditions
- Guidance strength
- Sampling schedule

---

## 4. Sampling step

A **sampling step** is one numerical update along the trajectory.

A simplified five-step view:

```text
Step 0: initial noise
Step 1: rough composition
Step 2: subjects and motion emerge
Step 3: recognizable scene
Step 4: detail improves
Step 5: final latent video
```

---

## 5. Why a solver is necessary

The model predicts velocity, but velocity is not yet the next state.

The solver decides:

- How far to move
- How to use the direction
- When to evaluate again
- How to estimate curvature
- How to limit numerical error

```text
Model:
Predicts how the state should change

Solver:
Calculates the next state
```

---

## 6. Few steps versus many steps

### Few large steps

- Faster
- Cheaper
- Greater approximation error
- More risk of incomplete detail or abrupt motion

### More smaller steps

- Slower
- More calculations
- Potentially better trajectory approximation
- Potentially better detail and stability

---

## 7. Too few steps

Possible symptoms:

- Incomplete subjects
- Soft detail
- Weak prompt adherence
- Abrupt motion
- Unstable faces
- Poor hands
- Background deformation
- Unfinished appearance

---

## 8. More steps and diminishing returns

More steps may improve:

- Detail
- Texture
- Prompt adherence
- Motion smoothness
- Temporal stability

But improvement often decreases after a point.

```text
10 steps → visibly incomplete
20 steps → major improvement
30 steps → moderate improvement
40 steps → slight improvement
50 steps → nearly unchanged
```

This is **diminishing returns**.

---

## 9. More steps cannot fix every failure

If the trajectory establishes two foxes instead of one, more steps may simply create two more detailed foxes.

```text
More accurate sampling
≠
automatic correction of scene composition
```

Change the prompt, seed, source image, or shot design when broad structure is wrong.

---

## 10. Numerical error

A solver approximates a continuous path.

The difference between the ideal path and the approximation is **numerical error**.

```text
Ideal trajectory:
smooth curve

Approximate trajectory:
series of estimated movements
```

---

## 11. Euler-style reasoning

The simplest conceptual approach:

```text
1. Inspect current state.
2. Predict current velocity.
3. Move a small distance in that direction.
4. Repeat.
```

Simplified update:

```text
Next state
=
current state
+
step size × predicted velocity
```

The key idea is to use the current direction to estimate the next position.

---

## 12. Euler analogy

Imagine walking on a curved path in fog.

You can only see the immediate direction.

Large steps may leave the path. Smaller steps follow the curve more accurately.

---

## 13. Predictor-corrector reasoning

A more advanced solver may:

1. Predict the next state.
2. Use additional information to correct the estimate.

This can reduce approximation error.

---

## 14. UniPC

**UniPC** is a predictor-corrector style sampling approach.

### Predictor

Estimate where the next state should be.

### Corrector

Refine that estimate using more information.

The goal is to follow the trajectory accurately with a practical number of steps.

---

## 15. DPM++

**DPM++** refers to a family of advanced diffusion-style sampling methods.

Conceptually, they aim to:

- Approximate the trajectory efficiently
- Use model predictions effectively
- Produce strong quality at practical step counts
- Reduce some errors of simpler methods

Different variants may behave differently.

---

## 16. Solver choice affects output

Changing only the solver may change:

- Fine detail
- Contrast
- Motion smoothness
- Prompt adherence
- Texture
- Temporal stability
- Artifact type
- Overall appearance

The solver is part of the complete generation configuration.

---

## 17. Reproducibility

To reproduce an experiment, record:

- Model
- Workflow
- Prompt
- Source image
- Audio
- Seed
- Resolution
- Frame count
- Sampling steps
- Solver
- Guidance
- Schedule-related settings

Same seed plus a different solver may produce a different result.

---

## 18. Step count and solver must be tested together

```text
20 steps with solver A
may not equal
20 steps with solver B
```

One solver may work better at lower step counts. Another may require more steps.

---

## 19. Speed–quality trade-off

```text
Fewer steps:
faster, cheaper, potentially rougher

More steps:
slower, more expensive, potentially more refined
```

The best setting must be discovered experimentally.

---

## 20. Draft versus production

### Draft

Evaluate:

- Subject count
- Composition
- Movement direction
- Camera behavior
- General prompt interpretation

Use lower cost and several seeds.

### Production

Evaluate:

- Detail
- Texture
- Face
- Motion smoothness
- Temporal stability

Use the selected prompt, seed, solver, and step count.

---

## 21. Controlled experiments

Change only one variable.

### Step-count experiment

Keep model, prompt, seed, resolution, frame count, solver, and guidance fixed.

Change only steps.

### Solver experiment

Keep prompt, seed, resolution, frame count, step count, and guidance fixed.

Change only solver.

---

## 22. Evaluation criteria

### Structure

- Correct subject count
- Correct major objects
- Correct framing

### Prompt adherence

- Correct subject
- Correct action
- Correct environment

### Motion

- Smoothness
- Correct order
- No teleportation
- Stable camera

### Detail

- Face
- Hands
- Hair
- Clothing
- Background

### Temporal consistency

- Stable identity
- Stable color
- Stable background
- Stable object shape

### Cost

- Generation time
- Memory demand
- Practical production value

---

## 23. Sampling schedule versus solver

```text
Sampling schedule:
Where along the trajectory updates occur

Solver:
How movement between those points is calculated

Step count:
How many updates are used
```

---

## 24. Plain-language explanation

Imagine refining a painting.

The model tells you the direction of improvement.

The solver decides how to apply each improvement.

The step count determines how many times you stop and refine the work.

Too few stops may leave it unfinished. Too many may add little after a point.

---

## 25. Important terminology

| Term | Meaning |
|---|---|
| Sampling | Generating a new result |
| Sampling step | One update along the trajectory |
| Step count | Number of updates |
| Numerical solver | Method approximating the trajectory |
| Step size | Distance covered by one update |
| Numerical error | Difference between ideal and approximate paths |
| Euler-style solver | Uses current velocity for the next estimate |
| Predictor | Initial estimate of the next state |
| Corrector | Refinement of that estimate |
| UniPC | Predictor-corrector sampling approach |
| DPM++ | Family of advanced sampling methods |
| Diminishing returns | Smaller gains from additional steps |
| Controlled experiment | Test changing one variable at a time |

---

## 26. Practice activity

Compare low, medium, and high sampling-step runs for the same fox shot.

Evaluate:

- Generation speed
- Fox detail
- Motion smoothness
- Background stability
- Prompt adherence
- Overall value

---

## 27. Expected result

| Category | Low steps | Medium steps | High steps |
|---|---|---|---|
| Speed | Fastest | Moderate | Slowest |
| Detail | Weak | Good | Slightly better |
| Motion | Rough | Improved | Similar or improved |
| Stability | Lower | Better | Similar or slightly better |
| Overall use | Drafting | Best balance | Final comparison |

This is a hypothesis. Real results must be measured.

---

## 28. Failure analysis

### Video looks unfinished
Too few steps may be used.

### Slow generation with little improvement
Diminishing returns.

### Wrong composition remains at high steps
Broad trajectory is incorrect.

### Invalid solver comparison
Different seeds or settings were used.

### Same steps behave differently under another solver
Step count depends on solver behavior.

### High detail but unstable motion
Evaluate temporal quality, not single-frame sharpness only.

---

## 29. Short quiz

1. What is a sampling step?
2. What does a solver do?
3. What is Euler-style reasoning?
4. What does predictor-corrector mean?
5. What is UniPC?
6. What is DPM++?
7. Do more steps always guarantee better quality?
8. Why keep the same seed in a solver comparison?

---

## 30. Quiz answers

1. One update along the trajectory.
2. It approximates movement through the learned field.
3. It uses the current velocity to estimate the next state.
4. Predict, then refine the estimate.
5. A predictor-corrector sampling approach.
6. A family of advanced sampling methods.
7. No.
8. To isolate the solver’s effect.

---

## 31. Completion checklist

- [ ] I understand sampling and sampling steps.
- [ ] I understand why a solver is necessary.
- [ ] I can explain numerical error.
- [ ] I can explain Euler-style stepping.
- [ ] I understand predictor-corrector reasoning.
- [ ] I understand UniPC conceptually.
- [ ] I understand DPM++ conceptually.
- [ ] I understand diminishing returns.
- [ ] I know why more steps cannot always fix structure.
- [ ] I can design a controlled step-count experiment.
- [ ] I can design a controlled solver experiment.
- [ ] I know the difference between schedule, solver, and step count.
