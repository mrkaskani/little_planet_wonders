# Module 6

## Lesson 22 of 40 — Common Command Parameters

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain the purpose of the common Wan generation parameters.
- Group parameters by workflow, quality, reproducibility, output, and memory.
- Identify which settings must remain fixed during controlled experiments.
- Recognize invalid or contradictory parameter combinations.
- Build a complete generation-settings record without relying on implementation examples.

---

## 2. Parameters are generation controls

A parameter is a named setting supplied to the generation workflow.

Parameters answer questions such as:

- Which model workflow should run?
- Where are the model assets?
- What should the video contain?
- Is there an image or audio condition?
- How large and how long should the video be?
- How should sampling proceed?
- Which random starting state should be used?
- Where should the result be stored?
- Which memory-saving options should be enabled?

---

## 3. Parameter categories

The course groups common settings into six categories:

1. Workflow selection
2. Conditioning inputs
3. Output dimensions and duration
4. Sampling behavior
5. Reproducibility and output
6. Memory optimization

Keeping these categories separate makes experiments easier to reason about.

---

## 4. Common parameter reference

| Parameter | Purpose |
|---|---|
| `--task` | Select the model workflow |
| `--ckpt_dir` | Select the model-checkpoint directory |
| `--prompt` | Provide the text condition |
| `--image` | Provide the image condition |
| `--audio` | Provide the audio condition for speech-driven generation |
| `--size` | Define output dimensions or supported output size |
| `--frame_num` | Request a number of generated frames |
| `--sample_steps` | Set the number of sampling updates |
| `--sample_solver` | Select the numerical sampling method |
| `--sample_guide_scale` | Set prompt-guidance strength |
| `--sample_shift` | Adjust sampling-schedule behavior |
| `--base_seed` | Set the random starting seed |
| `--save_file` | Select the output destination |
| `--offload_model` | Move inactive model components to CPU memory |
| `--convert_model_dtype` | Use a lower parameter precision where supported |
| `--t5_cpu` | Place the text encoder on CPU |

These are the parameter names specified by the supplied course outline. Exact support can vary by model release and workflow.

---

## 5. `--task`

The task setting selects the generation workflow.

It determines which model behavior is expected, such as:

- Text-to-Video
- Image-to-Video
- Text-Image-to-Video
- Speech-to-Video

A task must match the selected checkpoint family.

Incorrect pairing may cause:

- Loading failure
- Missing conditioning support
- Shape incompatibility
- Incorrect configuration

---

## 6. `--ckpt_dir`

This setting identifies the checkpoint directory.

The directory must contain the model assets required for the selected workflow.

Review:

```text
Task selects the workflow.
Checkpoint directory supplies the trained model.
```

A correct prompt cannot compensate for the wrong checkpoint.

---

## 7. `--prompt`

The prompt provides text conditioning.

Depending on the workflow, it may describe:

- Subject
- Appearance
- Action
- Environment
- Camera
- Lighting
- Style
- Motion constraints
- Invariants

In T2V, the prompt carries most of the creative condition.

In I2V, it should focus more heavily on changes and motion.

In S2V, it directs acting, scene behavior, and camera control while audio supplies timing.

---

## 8. `--image`

The image setting supplies a visual condition.

It is central to:

- I2V
- Image-conditioned TI2V
- S2V

The image can strongly influence:

- Initial composition
- Character appearance
- Color palette
- Background
- Camera position
- Starting pose

It does not perfectly guarantee identity or ending pose throughout the clip.

---

## 9. `--audio`

The audio setting supplies speech or performance timing to S2V.

Audio may guide:

- Mouth timing
- Pauses
- Speech rhythm
- Energy
- Intonation
- Head and body rhythm

The audio condition should be prepared and reviewed before generation.

A poor recording can create weak synchronization even if the visual condition is strong.

---

## 10. `--size`

The size setting controls the requested output dimensions or selects a supported resolution profile.

It affects:

- Pixel dimensions
- Aspect ratio
- Composition
- Latent spatial dimensions
- Token count
- Memory use
- Generation time

Changing size can also alter the composition even when the seed remains fixed.

---

## 11. `--frame_num`

The frame-number setting determines the requested number of generated frames.

Frame count affects:

- Duration at a selected playback FPS
- Latent temporal length
- Motion capacity
- Attention workload
- Drift risk
- Memory use

Remember:

```text
Duration = frame count ÷ playback FPS
```

Frame count and playback FPS are related but not identical controls.

---

## 12. `--sample_steps`

This setting controls how many sampling updates are used to follow the generation trajectory.

Fewer steps generally mean:

- Faster generation
- Lower computational cost
- Greater risk of incomplete refinement

More steps may improve:

- Detail
- Prompt adherence
- Motion quality
- Stability

However, more steps can produce diminishing returns and cannot guarantee correction of structural mistakes.

---

## 13. `--sample_solver`

The solver determines how numerical updates are calculated along the trajectory.

Different solvers may affect:

- Detail
- Motion smoothness
- Texture
- Prompt adherence
- Stability
- Required step count

Solver and step count should be tested together.

---

## 14. `--sample_guide_scale`

Guidance strength controls how strongly the generation is pushed toward its conditions.

Lower guidance may provide:

- More freedom
- More natural variation
- Weaker prompt adherence

Higher guidance may provide:

- Stronger adherence
- More explicit subject or style matching
- Greater risk of harsh, overconstrained, or unstable output

The best value depends on the model, workflow, prompt, and shot.

---

## 15. `--sample_shift`

The shift setting adjusts aspects of the sampling schedule.

Conceptually, it can change how generation effort is distributed across the trajectory.

It may influence the balance between:

- High-noise structural work
- Middle-stage motion development
- Low-noise detail refinement

It should be changed only in controlled experiments because its effects interact with steps and solver.

---

## 16. `--base_seed`

The seed determines the random starting state.

Changing it may change:

- Composition
- Subject appearance
- Object placement
- Motion path
- Camera behavior
- Fine detail

A seed supports reproducibility only when the rest of the configuration is also recorded.

---

## 17. `--save_file`

This setting identifies where the generated result should be stored.

A good output destination should preserve:

- Shot identity
- Candidate identity
- Workflow
- Prompt version
- Seed

Avoid overwriting previous candidates.

---

## 18. `--offload_model`

Model offloading moves inactive components from GPU memory to CPU memory.

Possible benefit:

- Lower peak GPU-memory usage

Possible costs:

- Increased data transfer
- Longer generation time
- Greater CPU-memory demand
- More complex performance behavior

Offloading changes memory placement, not model quality by itself.

---

## 19. `--convert_model_dtype`

Reduced model precision stores or processes parameters using a smaller numerical representation where supported.

Possible benefits:

- Lower memory usage
- Faster computation on suitable hardware

Possible risks:

- Compatibility problems
- Numerical instability
- Small or significant quality differences depending on implementation

Reduced precision should be validated rather than assumed safe for every model component.

---

## 20. `--t5_cpu`

This option places the text encoder on CPU rather than GPU.

Possible benefit:

- Frees GPU memory for the video model and activations

Possible cost:

- Slower prompt encoding
- Additional CPU-memory use
- Transfer overhead

This option is most useful when GPU memory is the limiting resource.

---

## 21. Required versus optional inputs

| Workflow | Prompt | Image | Audio |
|---|---:|---:|---:|
| T2V | Required | No | No |
| I2V | Required | Required | No |
| TI2V text mode | Required | No | No |
| TI2V image mode | Required | Required | No |
| S2V | Required | Required | Required for recorded-speech workflow |

The course treats optional pose guidance separately from these core inputs.

---

## 22. Controlled experiment rule

When testing one parameter, keep the others fixed.

Example:

```text
Run A: baseline step count
Run B: higher step count
```

Keep fixed:

- Model
- Prompt
- Image
- Audio
- Resolution
- Frame count
- Solver
- Guidance
- Shift
- Seed

This isolates the effect of step count.

---

## 23. Invalid comparisons

An experiment is difficult to interpret when several settings change together.

Invalid comparison example:

```text
Run A:
low resolution, seed 10, solver A, short prompt

Run B:
high resolution, seed 80, solver B, expanded prompt
```

Any difference could be caused by multiple variables.

---

## 24. Parameter dependency map

```text
Task
└── must match checkpoint

Workflow
└── determines required inputs

Resolution + frame count
└── determine latent workload

Steps + solver + shift
└── determine trajectory approximation

Guidance + prompt
└── influence condition adherence

Seed + all other settings
└── define reproducible experiment state
```

---

## 25. Plain-language explanation

Think of the parameters as a production form.

The form tells the system:

- Which machine to use
- Which materials to provide
- What to create
- How large and long it should be
- How carefully the generation path should be followed
- Where the result should be stored
- How memory should be managed

Missing or contradictory entries make the production unreliable.

---

## 26. Important terminology

| Term | Meaning |
|---|---|
| Task | Selected generation workflow |
| Checkpoint directory | Location of trained model assets |
| Condition | Text, image, audio, or other guidance |
| Resolution | Width and height of output frames |
| Frame count | Number of generated frames |
| Sampling step | One numerical trajectory update |
| Solver | Method calculating sampling updates |
| Guidance scale | Strength of condition influence |
| Sampling shift | Adjustment to trajectory scheduling |
| Seed | Random starting-state identifier |
| Offloading | Moving inactive components to CPU memory |
| Reduced precision | Smaller numerical representation for model values |

---

## 27. Practical activity

Create a settings record for three shots:

1. T2V garden establishing shot
2. I2V character head-turn shot
3. S2V dialogue shot

For each, record:

- Required inputs
- Model family
- Resolution
- Frame count
- Sampling settings
- Seed
- Output identity
- Memory options

Do not select numerical values unless you have tested them; focus on completeness and dependencies.

---

## 28. Expected result

A strong settings record should make clear:

- Which model and task are paired
- Which conditions are required
- Which variables affect quality
- Which variables affect memory
- Which variables must be fixed for reproduction
- Which output belongs to which experiment

---

## 29. Failure analysis

### Failure 1 — Task and checkpoint mismatch

**Result:** The workflow cannot load or behaves incorrectly.

**Improvement:** Pair each task with its matching model family.

### Failure 2 — Same seed, different settings

**Result:** The video changes despite reusing the seed.

**Cause:** Seed is only one part of the generation state.

### Failure 3 — Excessive guidance

**Result:** Harsh, unstable, or unnatural output.

**Improvement:** Compare guidance values while fixing all other variables.

### Failure 4 — Frame count increased without memory planning

**Result:** Memory exhaustion or severe slowdown.

**Improvement:** Estimate latent temporal growth before generation.

### Failure 5 — Offloading assumed to be free

**Result:** Lower GPU memory but much slower generation.

**Improvement:** Evaluate both memory and total generation time.

---

## 30. Short quiz

1. What does `--task` select?
2. What must match the selected task?
3. What does `--frame_num` control?
4. What is the difference between steps and solver?
5. What does the seed control?
6. Why does the same seed not guarantee the same result after changing resolution?
7. What is the purpose of model offloading?
8. Which setting controls condition strength?

---

## 31. Quiz answers

1. The generation workflow.
2. The model checkpoint family and configuration.
3. The requested number of generated frames.
4. Steps define how many updates occur; the solver defines how updates are calculated.
5. The random starting state.
6. Resolution changes the generation configuration and latent structure.
7. To reduce GPU-memory usage by moving inactive components to CPU memory.
8. `--sample_guide_scale`.

---

## 32. Completion checklist

- [ ] I understand every common parameter in the course table.
- [ ] I can pair a task with the correct checkpoint.
- [ ] I know which workflows require images and audio.
- [ ] I understand frame count, steps, solver, guidance, shift, and seed.
- [ ] I can distinguish quality controls from memory controls.
- [ ] I can design a one-variable experiment.
- [ ] I understand why a seed alone is insufficient for reproduction.
- [ ] I can create a complete settings record for a shot.
