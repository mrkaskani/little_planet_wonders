# Module 7

## Lesson 24 of 40 — T2V Pipeline

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Trace the complete Text-to-Video pipeline.
- Explain the roles of the prompt, text encoder, latent noise, DiT, sampling process, and VAE decoder.
- Identify which stage is responsible for common failures.
- Explain why the model can generate many different videos from one prompt.
- Design a review process that follows the pipeline from structure to detail.

---

## 2. Official model covered

The course identifies the dedicated Wan Text-to-Video model as:

```text
Wan 2.2 T2V-A14B
```

T2V creates a new video from text without requiring an approved source image.

---

## 3. Core pipeline

```text
Prompt
→ text encoder
→ text embeddings
→ random latent video
→ flow-matching DiT / MoE denoiser
→ sampled latent video
→ VAE decoder
→ visible video
```

Each stage has a distinct responsibility.

---

## 4. Stage 1 — Prompt

The prompt defines the creative condition.

It may specify:

- Subject
- Appearance
- Action
- Environment
- Camera framing
- Camera movement
- Lighting
- Visual style
- Motion constraints

The prompt is not a frame-by-frame animation timeline.

It describes the intended result and leaves the model to infer missing visual and temporal details.

---

## 5. Stage 2 — Text encoding

The text encoder converts words into numerical embeddings.

Conceptually:

```text
Prompt words
→ tokenized text
→ contextual text representation
```

The embeddings preserve relationships such as:

- Which adjective describes which subject
- Which action belongs to which character
- Which object is the movement target
- Which camera language applies to the shot

---

## 6. Stage 3 — Random latent video

Generation begins from random latent noise.

The starting state contains no complete visible video.

It provides variation, allowing the same prompt to produce multiple valid possibilities.

Changing the seed may change:

- Composition
- Character appearance
- Motion
- Object placement
- Camera behavior

---

## 7. Stage 4 — Flow-matching DiT

The Diffusion Transformer processes latent video tokens and conditions.

It receives information such as:

- Current latent state
- Current generation timestep
- Text embeddings
- Sampling guidance

It predicts how the latent state should move through the generation trajectory.

---

## 8. Stage 5 — Mixture-of-Experts specialization

For the A14B family described in the course:

```text
High-noise stage
→ high-noise expert
→ structure, composition, major motion

Low-noise stage
→ low-noise expert
→ appearance, texture, fine detail
```

The expert choice follows the denoising stage rather than routing each video token independently.

---

## 9. Stage 6 — Sampling

A numerical solver follows the model-predicted trajectory using a finite number of steps.

Sampling settings influence:

- Trajectory accuracy
- Detail
- Motion smoothness
- Prompt adherence
- Generation time

The solver does not invent the prompt meaning; it approximates movement through the learned flow.

---

## 10. Stage 7 — Generated latent video

After sampling, the result is still a compressed latent video.

It should contain the generated:

- Scene structure
- Subject appearance
- Motion
- Camera behavior
- Temporal relationships

It is not yet the visible pixel output.

---

## 11. Stage 8 — VAE decoding

The VAE decoder reconstructs visible frames from the generated latent video.

It produces:

- Pixel colors
- Texture
- Object boundaries
- Visible fine detail
- Final frame sequence

Decoder reconstruction can introduce softness, shimmer, or fine-detail artifacts.

---

## 12. Condition flow

```text
Prompt
   │
   ▼
Text embeddings
   │
   ├──────────────┐
   │              │
   ▼              ▼
Cross-attention   Timestep-conditioned processing
   │              │
   └──────┬───────┘
          ▼
Generated latent trajectory
```

Text influences generation repeatedly, not only at the beginning.

---

## 13. Structure emerges before detail

Early stages establish:

- Subject count
- Composition
- Environment
- Major movement
- Camera framing

Later stages refine:

- Face
- Hair
- Clothing
- Texture
- Lighting detail

A structurally incorrect video can become beautifully detailed but remain unusable.

---

## 14. T2V has high creative freedom

Because no source image fixes the first frame, T2V can invent:

- Character design
- Location layout
- Object placement
- Color palette
- Camera angle
- Motion path

This makes it strong for exploration and weaker for exact recurring identity.

---

## 15. Typical T2V use cases

- Establishing shots
- Landscapes
- New environments
- Atmospheric transitions
- Background action
- Shots where exact recurring identity is unnecessary
- Early visual exploration

---

## 16. Pipeline failure map

| Failure | Likely area |
|---|---|
| Prompt concept missing | Prompt interpretation or conditioning |
| Two subjects instead of one | High-noise structure |
| Wrong camera framing | Early composition |
| Action direction wrong | Motion planning or prompt ambiguity |
| Face flickers | Low-noise detail or temporal consistency |
| Texture is soft | Low-noise refinement or VAE decoding |
| Video changes after seed change | Random starting state |

These are diagnostic categories, not guaranteed internal proofs.

---

## 17. Review order

Review a T2V candidate in this sequence:

1. Correct subject count
2. Correct major objects
3. Correct environment
4. Correct composition
5. Correct action and direction
6. Camera behavior
7. Temporal consistency
8. Fine visual detail
9. Overall aesthetics

Do not begin with texture if the scene structure is wrong.

---

## 18. Plain-language explanation

Imagine giving a film crew a written brief but no actors, set, or storyboard image.

The crew must:

- Interpret the brief
- Cast the subject
- Build the environment
- Plan the camera
- Perform the action
- Finish the visual details

T2V gives the model the same broad freedom.

---

## 19. Important terminology

| Term | Meaning |
|---|---|
| T2V | Text-to-Video |
| Text embedding | Numerical representation of prompt meaning |
| Latent noise | Random compressed starting state |
| DiT | Diffusion Transformer |
| Flow matching | Learning the direction from noise toward video data |
| Sampling | Following the generation trajectory |
| High-noise expert | Structural-stage specialist |
| Low-noise expert | Detail-stage specialist |
| Latent video | Compressed generated video representation |
| VAE decoder | Component reconstructing visible frames |

---

## 20. Relevant settings

- Task
- Checkpoint directory
- Prompt
- Resolution
- Frame count
- Sampling steps
- Solver
- Guidance strength
- Sampling shift
- Seed
- Output destination
- Memory options

A reproducible T2V result requires all important settings, not only the prompt.

---

## 21. Practical activity

Trace this prompt through the pipeline:

```text
One small red fox walks slowly through a bright garden,
pauses beside a blue watering can, and looks toward the camera.
Medium-wide eye-level shot, fixed camera, soft morning light.
```

For each stage, describe what information is created or transformed.

---

## 22. Expected result

### Prompt stage

Defines subject, count, action, environment, camera, and lighting.

### Text-encoding stage

Creates contextual embeddings for concepts such as red fox, walking, garden, watering can, pause, and fixed camera.

### High-noise stage

Establishes one fox, one watering can, garden composition, movement direction, and camera framing.

### Middle stage

Develops walking, pause, head turn, and object relationships.

### Low-noise stage

Refines fur, face, flowers, watering-can detail, and local stability.

### Decoder stage

Reconstructs visible frames and final texture.

---

## 23. Failure analysis

### Failure 1 — One prompt produces different foxes

**Cause:** Different random starting states and high creative freedom.

### Failure 2 — Correct scene but no pause

**Cause:** Multi-stage action may be too complex or weakly represented.

**Improvement:** Simplify or divide the shot.

### Failure 3 — Strong detail but wrong camera

**Cause:** Early composition failure.

**Improvement:** Strengthen framing language or use another seed.

### Failure 4 — Background changes over time

**Cause:** Temporal consistency failure.

**Improvement:** Use a fixed camera, simpler background, or shorter shot.

### Failure 5 — Soft final video

**Possible causes:** Low-noise refinement, resolution, or VAE reconstruction.

---

## 24. Short quiz

1. What is the first creative input in T2V?
2. What does the text encoder produce?
3. Why does generation begin from random latent noise?
4. What does the high-noise expert prioritize?
5. What does the low-noise expert prioritize?
6. What is the solver’s role?
7. What converts latent video into visible frames?
8. Why is T2V weak for exact recurring identity?

---

## 25. Quiz answers

1. The text prompt.
2. Contextual text embeddings.
3. To provide a variable starting state for generation.
4. Structure, composition, and major movement.
5. Appearance, texture, and fine detail.
6. To approximate movement through the generation trajectory.
7. The VAE decoder.
8. No source image fixes the character’s exact visual identity.

---

## 26. Completion checklist

- [ ] I can trace the T2V pipeline end to end.
- [ ] I understand the role of text embeddings.
- [ ] I understand random latent initialization.
- [ ] I know what the DiT and MoE experts do.
- [ ] I understand sampling and decoding.
- [ ] I can attribute common failures to pipeline stages.
- [ ] I can review a result from structure to detail.
- [ ] I know when T2V is an appropriate workflow.
