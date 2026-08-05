# Module 2

## Lesson 6 of 40 — Flow Matching

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain flow matching in plain language.
- Explain how it transforms noise into video data.
- Understand a probability path.
- Explain a velocity field.
- Interpret a simplified path equation.
- Understand the ODE interpretation.
- Distinguish flow matching from noise prediction.
- Identify trajectory failures.

---

## 2. Main idea

Flow matching teaches a model how to move an internal representation from a noise distribution toward a realistic video distribution.

```text
Noise distribution
→ learn the direction of movement
→ follow a transformation path
→ video distribution
```

The model predicts a **velocity field**.

The central question is:

> In which direction should the current state move so that it becomes more like realistic video data?

---

## 3. Distributions

A **distribution** describes a range of possible samples and their likelihood.

### Noise distribution

Contains random, unstructured samples.

### Video-data distribution

Contains structured representations of realistic videos.

The goal is not to map one noise sample to one predetermined video. It is to learn a general transformation from many noise samples to many plausible video samples.

---

## 4. Plain-language explanation

Imagine random particles floating in space.

The model learns arrows that tell each particle how to move.

```text
Random particles
→ begin organizing
→ form large shapes
→ form subjects and motion
→ produce detailed video
```

Each arrow says:

```text
From this current state,
move in this direction.
```

---

## 5. Probability path

A **probability path** is a sequence of intermediate distributions connecting noise to real data.

```text
Time 0.00: noise
Time 0.25: mostly noise with weak structure
Time 0.50: partial subjects and movement
Time 0.75: recognizable video with incomplete detail
Time 1.00: video-data distribution
```

This is generation time, not playback time.

---

## 6. Two meanings of time

### Generation time

Progress from noise to completed result.

### Video time

Events inside the generated video.

```text
Generation time:
Noise → partial result → completed video

Video time:
Character stands → walks → stops
```

---

## 7. Simplified path equation

```text
x(t) = (1 − t)x₀ + tx₁
```

Where:

- `x₀` = noise sample
- `x₁` = clean data sample
- `t` = position along the path
- `x(t)` = intermediate state

### At `t = 0`

```text
x(0) = x₀
```

Entirely noise.

### At `t = 1`

```text
x(1) = x₁
```

Clean data endpoint.

### At `t = 0.5`

The state lies halfway along the simplified path.

The equation is a teaching model, not a literal visible pixel average in production generation.

---

## 8. Velocity

Velocity describes direction and rate of change.

In flow matching:

```text
The latent-video state changes
according to a predicted velocity.
```

A **velocity field** assigns a direction to many possible states.

```text
Current state
+
generation time
+
conditions
→ predicted velocity
```

---

## 9. Conditioning changes the flow

The same starting noise can follow different trajectories under different conditions.

```text
Same noise + fox prompt → fox-video trajectory
Same noise + boat prompt → boat-video trajectory
```

Text, image, audio, and pose guidance influence the predicted direction.

---

## 10. Flow-matching training

A simplified training process:

```text
1. Select a real video representation.
2. Select a noise sample.
3. Select generation time t.
4. Construct an intermediate point.
5. Determine the desired movement direction.
6. Ask the model to predict that direction.
7. Compare prediction with target velocity.
8. Adjust the model.
```

For a simplified straight path, the target direction is related to:

```text
x₁ − x₀
```

---

## 11. Generation with learned flow

```text
1. Begin with random latent noise.
2. Predict velocity at the current state.
3. Move slightly in that direction.
4. Advance generation time.
5. Predict a new velocity.
6. Repeat until the final state.
```

The velocity changes because the model’s priorities change from structure to detail.

---

## 12. ODE interpretation

Flow matching can be described using an ordinary differential equation:

```text
dx/dt = v(x, t)
```

Where:

- `x` = current internal state
- `t` = generation time
- `v` = predicted velocity
- `dx/dt` = how the state changes as time changes

A numerical solver follows this field over time.

---

## 13. Latent velocity versus visible motion

Latent velocity is not the same as a character’s physical speed.

It describes movement in the internal generation space.

That internal movement eventually produces:

- Character motion
- Camera motion
- Appearance
- Scene structure
- Texture
- Temporal consistency

---

## 14. Flow matching versus noise prediction

### Noise-prediction view

```text
Current noisy state
→ estimate noise
→ move toward cleaner data
```

### Flow-matching view

```text
Current state
→ estimate transformation velocity
→ follow the flow toward data
```

Simplified distinction:

```text
Noise prediction:
What noise is present?

Flow matching:
Which direction should the state move now?
```

---

## 15. Why flow matching is useful

Conceptual advantages:

- Direct velocity prediction
- Continuous-time interpretation
- Compatibility with ODE sampling
- Flexible paths
- Clear separation between path and solver

Actual performance still depends on model architecture, training, solver, step count, resolution, frame count, and conditioning.

---

## 16. High-noise and low-noise behavior

### High noise

- Scene composition
- Subject count
- Camera framing
- Major object locations
- Large motion
- Broad temporal structure

### Low noise

- Facial appearance
- Hair and clothing
- Texture
- Hand shape
- Fine lighting
- Local temporal stability

---

## 17. Path, velocity, and solver

```text
Probability path:
Where the process should travel

Velocity field:
Which direction to move

Solver:
How to take practical numerical steps
```

This distinction is essential for understanding sampling.

---

## 18. Plain-language analogy

Imagine driving along a curved mountain road.

- Road = probability path
- Direction signs = velocity field
- Navigation method = solver
- Destination = realistic video data

Too few large movements may cut across the road. More small movements may follow it more accurately.

---

## 19. Important terminology

| Term | Meaning |
|---|---|
| Flow matching | Learning a transformation velocity |
| Distribution | Range and likelihood of samples |
| Noise distribution | Collection of random starting samples |
| Data distribution | Collection of realistic video samples |
| Probability path | Sequence connecting noise and data |
| Generation time | Progress from noise to final result |
| Velocity | Direction and rate of state change |
| Velocity field | Function assigning velocity to states and times |
| Target velocity | Correct transformation direction during training |
| ODE | Equation describing continuous change |
| Numerical solver | Method approximating the trajectory |
| Latent velocity | Movement in internal representation space |

---

## 20. Relevant generation concepts

| Concept | Relevance |
|---|---|
| Random seed | Determines initial noise |
| Prompt | Influences destination and trajectory |
| Source image | Constrains appearance and structure |
| Speech audio | Guides temporal performance |
| Sampling steps | Number of practical updates |
| Sampling solver | Numerical approximation method |
| Sampling shift | Adjusts trajectory behavior |
| Guidance strength | Changes condition influence |
| High-noise expert | Structural trajectory stages |
| Low-noise expert | Detail trajectory stages |

---

## 21. Practice activity

Explain flow matching in two ways.

### Beginner explanation

Use:

- Random starting state
- Direction arrows
- Gradual movement
- Final organized video

### Technical explanation

Use:

- Noise distribution
- Data distribution
- Probability path
- Intermediate state
- Velocity field
- ODE
- Numerical solver

---

## 22. Expected explanations

### Beginner

The model starts with random information and follows learned directions. Early changes create the main scene and movement. Later changes improve details.

### Technical

Flow matching defines a probability path between noise and video-data distributions. The model learns the target velocity at intermediate states. During generation, a solver follows the learned field from noise toward a video latent.

---

## 23. Path-position exercise

For:

```text
x(t) = (1 − t)x₀ + tx₁
```

describe:

- `t = 0`
- `t = 0.25`
- `t = 0.5`
- `t = 0.75`
- `t = 1`

### Answers

- `t = 0`: noise endpoint
- `t = 0.25`: closer to noise
- `t = 0.5`: halfway
- `t = 0.75`: closer to clean data
- `t = 1`: clean-data endpoint

---

## 24. Failure analysis

### Wrong composition
Early trajectory moved toward the wrong global structure.

### Weak intermediate motion
Trajectory may be too coarse or action too complex.

### Image-driven result is too static
Insufficient temporal change.

### Character and background drift
Trajectory changes too much.

### Good face becomes distorted late
Low-noise trajectory instability.

### More steps do not repair scene structure
More accurate movement along a wrong trajectory still leads to the wrong destination.

---

## 25. Short quiz

1. What does flow matching predict?
2. What does a probability path connect?
3. What does the velocity field describe?
4. What does `x₀` represent?
5. What happens at `t = 1`?
6. What does the ODE describe?
7. What does a numerical solver do?
8. Is latent velocity the same as visible physical speed?

---

## 26. Quiz answers

1. A transformation velocity.
2. Noise and data distributions.
3. How the current state should change.
4. Noise.
5. The clean-data endpoint is reached.
6. Continuous change of the current state.
7. It approximates movement through the learned field.
8. No.

---

## 27. Completion checklist

- [ ] I can explain flow matching.
- [ ] I understand noise and data distributions.
- [ ] I understand a probability path.
- [ ] I understand generation time versus video time.
- [ ] I understand `x₀`, `x₁`, and `t`.
- [ ] I can explain velocity and velocity fields.
- [ ] I understand conditioning’s effect on the flow.
- [ ] I understand the ODE interpretation.
- [ ] I understand the role of a solver.
- [ ] I can distinguish latent velocity from visible motion.
- [ ] I can explain the difference between flow matching and noise prediction.
