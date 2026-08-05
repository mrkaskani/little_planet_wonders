# Module 2

## Lesson 5 of 40 — Diffusion Models

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain the forward noising process.
- Explain the reverse denoising process.
- Describe the purpose of a noise schedule.
- Distinguish training from generation.
- Explain what the model learns during training.
- Explain how conditions guide denoising.
- Identify common diffusion-related failures.

---

## 2. Main idea

A diffusion model learns how to transform noise into structured data.

```text
Training:
Clean video
→ progressively add noise
→ teach the model how to recover useful information

Generation:
Random noise
→ progressively refine it
→ generated video
```

---

## 3. Forward process

The forward process gradually adds noise to clean data.

```text
Clean video
→ slightly noisy
→ moderately noisy
→ heavily noisy
→ almost pure noise
```

It is mainly used to construct training examples.

At low noise, the scene remains recognizable but fine detail weakens.

At medium noise, body shapes and background relationships become uncertain.

At high noise, most visible structure is lost.

---

## 4. Why add noise during training?

The model learns patterns such as:

- Human and object structure
- Motion progression
- Frame relationships
- Lighting
- Prompt-to-video relationships
- Image-to-motion relationships
- Speech-to-performance relationships

Different noise levels create different learning difficulties.

At high noise, the model must recover broad structure.

At low noise, it must recover detail.

---

## 5. Reverse process

The reverse process transforms a noisy representation toward generated video.

```text
Noise
→ rough video structure
→ recognizable scene
→ refined movement
→ detailed video
```

The model repeatedly predicts how the current state should change.

---

## 6. Denoising is generative

Denoising is not simply cleaning an already hidden video.

At the start, there is no finished video behind the noise.

The model must construct:

- Subject appearance
- Scene composition
- Movement
- Camera behavior
- Temporal relationships
- Condition adherence

---

## 7. Noise level and timestep

A **timestep** indicates the current position in the diffusion process.

```text
High-noise timestep:
Focus on composition and major motion.

Low-noise timestep:
Focus on texture and local stability.
```

The model must know the timestep because its task changes across the trajectory.

---

## 8. Noise schedule

A **noise schedule** defines how noise changes across the process.

It influences:

- How noisy each stage is
- How refinement progresses
- How work is distributed across structure, motion, and detail

An unsuitable schedule may contribute to:

- Weak global structure
- Incomplete refinement
- Excessive smoothing
- Poor prompt adherence
- Motion problems

---

## 9. Training objective

A **training objective** defines what the model is asked to predict.

The model receives:

- A clean training video
- A noisy version
- A timestep
- Relevant conditions

It learns information that moves the state toward realistic video data.

Depending on the design, the prediction target may involve:

- Noise
- Clean data
- Velocity
- A related transformation direction

---

## 10. Simplified training cycle

```text
1. Select a clean video.
2. Encode it into a latent representation.
3. Select a random noise level.
4. Add noise.
5. Give the noisy state to the model.
6. Provide timestep and conditions.
7. Ask the model to predict the target.
8. Compare prediction with the correct target.
9. Adjust model parameters.
```

This repeats across many videos and noise levels.

---

## 11. Why random noise levels are used

The model must work throughout the entire trajectory.

It must handle:

- Very noisy states
- Partially formed scenes
- Nearly finished videos

Training at varied noise levels teaches this broad capability.

---

## 12. Training versus inference

### Training

- Real clean videos are available.
- Correct targets are known.
- Model predictions are compared with targets.
- Model parameters are updated.

### Inference

- The model is already trained.
- No correct final video exists.
- Generation begins from noise.
- Conditions guide the result.
- Model parameters normally stay unchanged.

| Question | Training | Generation |
|---|---|---|
| Clean real video available? | Yes | No |
| Correct target available? | Yes | No single correct final video |
| Model parameters updated? | Yes | Normally no |
| Conditions used? | Yes | Yes |
| Main purpose | Learn behavior | Produce a video |

---

## 13. Conditions during training

To use conditions during generation, the model must learn their relationships during training.

### Text

Learns how descriptions correspond to visual scenes and actions.

### Image

Learns how a starting image relates to future motion.

### Audio

Learns how speech timing and energy relate to mouth, head, and body movement.

---

## 14. Conditional and less-conditioned behavior

### Conditional generation

The output follows supplied guidance.

### Less-conditioned behavior

The model relies more broadly on learned video patterns.

Guidance techniques can compare or combine these behaviors to strengthen condition adherence.

---

## 15. The model learns probability

A diffusion model learns statistical patterns, not one exact answer.

For:

```text
A dog runs across a field.
```

many dogs, fields, speeds, camera angles, and lighting choices are valid.

This is why generation contains variation.

---

## 16. Why multiple steps are used

A highly noisy state contains many uncertainties:

- Subject identity
- Subject count
- Composition
- Motion
- Texture
- Camera

Multiple refinement steps reduce uncertainty progressively.

```text
Early updates:
Reduce large uncertainty.

Middle updates:
Develop subjects and movement.

Final updates:
Improve detail and consistency.
```

More steps do not always guarantee a better result. Diminishing returns and structural errors still occur.

---

## 17. Video diffusion versus image diffusion

Video diffusion must organize information across:

- Width
- Height
- Time

It must maintain identity and object permanence while generating motion.

```text
Change enough to create movement
but
remain stable enough to preserve identity
```

---

## 18. Plain-language explanation

Imagine covering a drawing with increasing fog.

During training, the model repeatedly practices understanding foggy versions of real videos.

During generation, it begins from something like complete fog and gradually constructs a plausible video that follows the instructions.

---

## 19. Important terminology

| Term | Meaning |
|---|---|
| Diffusion model | Model that learns a noise-to-data transformation |
| Forward process | Gradually adding noise to clean data |
| Reverse process | Transforming noise toward generated data |
| Noise level | Amount of corruption |
| Timestep | Position in the diffusion trajectory |
| Noise schedule | Rule controlling noise change |
| Training objective | Prediction task used to train the model |
| Training | Adjusting model parameters from examples |
| Inference | Using a trained model to generate output |
| Conditional generation | Generation guided by text, image, or audio |
| Spatial structure | Relationships within frames |
| Temporal structure | Relationships and changes across time |

---

## 20. Relevant generation concepts

| Concept | Relevance |
|---|---|
| Sampling steps | Number of refinement updates |
| Sampling solver | Method used to move through the trajectory |
| Sampling shift | Adjusts sampling progression |
| Guidance strength | Influences condition adherence |
| Random seed | Defines the starting state |
| Prompt | Supplies semantic guidance |
| Source image | Supplies visual guidance |
| Speech audio | Supplies temporal performance guidance |
| High-noise expert | Specializes in early structural stages |
| Low-noise expert | Specializes in later detail stages |

---

## 21. Practice activity

For a video of a child placing a red ball into a wooden box, describe what remains at:

- Clean state
- Low noise
- Medium noise
- High noise

---

## 22. Expected answer

### Clean
Character, ball, box, action, background, texture, lighting, and motion are clear.

### Low noise
Broad structure remains; fingers, texture, and fine facial detail weaken.

### Medium noise
Approximate character shape, object positions, and broad movement may remain.

### High noise
Most meaningful information is difficult to identify.

---

## 23. Training-versus-generation exercise

Classify:

1. Real clean video is available.
2. Model receives a timestep.
3. Model receives a text condition.
4. Model parameters are updated.
5. Process begins from random noise to create a new video.
6. Model processes noisy representations.

### Answers

| Statement | Answer |
|---|---|
| Real clean video available | Training |
| Timestep provided | Both |
| Text condition provided | Both |
| Parameters updated | Training |
| Starts from noise to create video | Generation |
| Processes noisy states | Both |

---

## 24. Failure analysis

### Good detail but wrong composition
Global structure was incorrect early.

### Correct composition but unfinished detail
Low-noise refinement may be insufficient.

### Weak prompt adherence
Prompt may be ambiguous or conditioning too weak.

### Static result
Motion instructions may be too weak or preservation too strong.

### Excessive uncontrolled movement
Conditions may be ambiguous or temporal generation unstable.

### More steps do not fix subject count
The structural error was established early.

---

## 25. Short quiz

1. What happens during the forward process?
2. What happens during the reverse process?
3. What does a noise schedule control?
4. What is training for?
5. What is inference?
6. During which process is a known clean target available?
7. Why use multiple refinement steps?
8. Can more steps always fix the wrong number of characters?

---

## 26. Quiz answers

1. Noise is progressively added to clean data.
2. A noisy state is transformed toward generated video.
3. How noise changes across the trajectory.
4. To adjust model parameters so the model learns useful behavior.
5. Using the trained model to generate output.
6. Training.
7. To reduce uncertainty progressively.
8. No.

---

## 27. Completion checklist

- [ ] I understand forward noising.
- [ ] I understand reverse denoising.
- [ ] I can explain noise levels and timesteps.
- [ ] I can explain a noise schedule.
- [ ] I understand a training objective.
- [ ] I can distinguish training from inference.
- [ ] I understand why conditions are learned during training.
- [ ] I understand why multiple steps are used.
- [ ] I understand why more steps do not always fix structural errors.
- [ ] I understand why video diffusion must model space and time.
