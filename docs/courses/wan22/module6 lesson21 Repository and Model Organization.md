# Module 6

## Lesson 21 of 40 — Repository and Model Organization

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Distinguish model source files from model checkpoint files.
- Explain the purpose of configuration, input, output, and reference folders.
- Design a clean project structure for Wan experiments.
- Record enough metadata to reproduce a generation.
- Avoid mixing model assets, project assets, and generated results.
- Identify common organization failures before production begins.

---

## 2. Why organization matters

Video generation produces many related assets:

- Model files
- Prompts
- Source images
- Speech audio
- Pose references
- Draft videos
- Approved videos
- Experiment notes
- Evaluation reports

Without a consistent structure, it becomes difficult to answer basic questions:

- Which model created this video?
- Which source image was used?
- Which seed and sampling settings were selected?
- Is this a draft or an approved result?
- Which prompt version produced the best motion?
- Can the result be reproduced later?

Organization is therefore part of technical reproducibility, not merely file cleanliness.

---

## 3. Course-specific Wan facts

The course covers these model families:

| Model | Primary workflow |
|---|---|
| Wan 2.2 T2V-A14B | Text-to-Video |
| Wan 2.2 I2V-A14B | Image-to-Video |
| Wan 2.2 TI2V-5B | Text-to-Video or Image-to-Video drafting |
| Wan 2.2 S2V-14B | Speech-driven video |

Each model family requires its matching checkpoint assets and workflow configuration.

A checkpoint for one model family should not be treated as interchangeable with another.

---

## 4. Source repository

The **source repository** contains the project logic and supporting files used to operate the model.

It may contain:

- Model architecture definitions
- Workflow configuration
- Input-processing logic
- Sampling logic
- VAE integration
- Text, image, or audio conditioning logic
- Example assets
- Documentation
- Dependency information

The source repository describes **how the system operates**.

It normally does not contain all large trained model weights directly.

---

## 5. Model checkpoint directory

The **checkpoint directory** contains the trained numerical parameters required by a model.

Conceptually:

```text
Model architecture
+
trained checkpoint parameters
=
usable trained model
```

The checkpoint directory may include separate assets for:

- The main video model
- The text encoder
- The video VAE
- Model configuration
- Tokenizer resources
- Audio components for speech-driven workflows

The exact contents depend on the model family.

---

## 6. Source code versus model weights

| Source repository | Model checkpoints |
|---|---|
| Defines operations and workflow | Stores learned numerical parameters |
| Usually much smaller | Usually much larger |
| Can be read and modified | Not meaningfully edited by hand |
| Describes architecture | Contains learned capability |
| Shared across some workflows | Specific to a model family or version |

A repository without the correct weights cannot generate using that trained model.

Weights without compatible source and configuration cannot be used correctly.

---

## 7. Configuration

A configuration describes how a model and workflow should be assembled.

It may define:

- Model family
- Latent dimensions
- VAE selection
- Text-encoder selection
- Supported resolutions
- Sampling defaults
- Expert behavior
- Precision choices
- Memory-related options

Configuration should be treated as part of the reproducible experiment state.

Changing configuration can change the output even when the prompt and seed remain the same.

---

## 8. Example inputs

Example-input folders help establish valid input formats and useful starting points.

They may contain:

- Text prompts
- Reference images
- Speech audio
- Pose videos
- Expected aspect ratios
- Example metadata

Example inputs should be copied into a separate project workspace before modification.

This preserves the original reference material.

---

## 9. Generated outputs

Generated outputs should be separated from source assets.

Useful output categories include:

```text
Drafts
Candidates
Rejected
Approved
Upscaled
Edited
Final
```

A generated file should not be overwritten simply because a new experiment uses the same prompt.

Every meaningful candidate should receive a unique identity.

---

## 10. Recommended project structure

```text
wan-project/
├── models/
│   ├── t2v-a14b/
│   ├── i2v-a14b/
│   ├── ti2v-5b/
│   └── s2v-14b/
├── references/
│   ├── characters/
│   ├── locations/
│   ├── props/
│   ├── audio/
│   └── pose/
├── prompts/
│   ├── drafts/
│   └── approved/
├── experiments/
│   ├── shot-s001/
│   ├── shot-s002/
│   └── shot-s003/
├── outputs/
│   ├── drafts/
│   ├── approved/
│   └── final/
└── reports/
    ├── experiment-log.md
    └── evaluation-notes.md
```

This is a production organization pattern, not a mandatory Wan internal layout.

---

## 11. Separate shared assets from project assets

### Shared assets

Used across many projects:

- Model checkpoints
- Common style references
- General templates
- Evaluation forms

### Project assets

Specific to one production:

- Character images
- Location references
- Shot prompts
- Dialogue
- Generated candidates
- Approval notes

Keeping them separate prevents accidental changes to shared model resources.

---

## 12. Shot-based organization

For multi-shot production, organize experiments by shot identity.

Example:

```text
shot-s010/
├── source/
├── prompts/
├── candidates/
├── reviews/
└── approved/
```

The shot folder should contain everything required to explain how that shot was produced.

---

## 13. Generation metadata

Record at least:

- Shot ID
- Model family
- Model version
- Prompt version
- Source-image version
- Audio version when applicable
- Resolution
- Frame count
- Playback FPS
- Seed
- Sampling steps
- Solver
- Guidance strength
- Schedule-related setting
- Generation date
- Review result

Metadata converts an attractive result into a reproducible technical asset.

---

## 14. Naming generated candidates

A useful name communicates identity without becoming excessively long.

Example pattern:

```text
S010_t2v_prompt03_seed0042_candidate02.mp4
```

Meaning:

- `S010`: shot identity
- `t2v`: workflow
- `prompt03`: prompt version
- `seed0042`: random seed
- `candidate02`: candidate number

Do not place the complete prompt inside the filename.

Store long descriptions in metadata or a report.

---

## 15. Versioning prompts and source images

Use explicit versions:

```text
prompt-v01
prompt-v02
prompt-v03-approved
```

```text
roxana-front-v01
roxana-front-v02-corrected
roxana-front-v03-approved
```

Avoid ambiguous labels such as:

```text
final
final-new
final-real
final-last
```

A file can be approved at one production stage and later replaced, so version numbers remain useful.

---

## 16. Model-version compatibility

A generation environment is reproducible only when the model version and supporting files are compatible.

Possible compatibility problems include:

- Checkpoint from a different model family
- Configuration from another release
- Incompatible VAE assets
- Missing text-encoder resources
- Incorrect speech components
- Changed default settings

Record the complete model identity instead of writing only “Wan 2.2.”

---

## 17. Plain-language explanation

Think of the source repository as a machine design and the checkpoint as the trained experience inside the machine.

The project folder contains the raw materials and production history.

```text
Machine design
+
trained knowledge
+
project inputs
+
recorded settings
=
reproducible generation workflow
```

If one part is missing, reproducing the result becomes difficult.

---

## 18. Important terminology

| Term | Meaning |
|---|---|
| Source repository | Files defining how the model workflow operates |
| Checkpoint | Trained numerical model parameters |
| Configuration | Settings defining model structure and behavior |
| Model family | Related model designed for a particular workflow |
| Project workspace | Folder containing production-specific assets |
| Candidate | One generated result under review |
| Approved output | Candidate selected for production |
| Metadata | Information describing how an asset was produced |
| Versioning | Assigning explicit revisions to changing assets |
| Reproducibility | Ability to recreate a result using recorded conditions |
| Shot ID | Stable identifier for one planned production shot |

---

## 19. Practical activity

Design a folder structure for this project:

```text
Five-shot sequence
One recurring character
One garden location
One speaking shot
Two T2V drafts
Two I2V character shots
One S2V dialogue shot
```

Your structure should separate:

- Models
- Shared references
- Shot-specific references
- Prompts
- Audio
- Candidates
- Approved results
- Evaluation reports

---

## 20. Expected result

A strong solution should make it possible to answer:

- Which workflow belongs to each shot?
- Which input files were used?
- Which results were rejected?
- Which result was approved?
- Which settings produced the approved version?
- Can another person locate every required asset?

---

## 21. Failure analysis

### Failure 1 — Checkpoints mixed with outputs

**Problem:** Generated videos are stored inside the model directory.

**Risk:** Accidental deletion, difficult backups, and unclear ownership.

**Improvement:** Keep model assets read-only and project outputs separate.

### Failure 2 — Candidate files overwritten

**Problem:** Every run uses the same output name.

**Risk:** Earlier experiments disappear.

**Improvement:** Use shot, prompt, seed, and candidate identifiers.

### Failure 3 — Prompt stored only in memory

**Problem:** The best output exists, but the exact prompt was not recorded.

**Risk:** The shot cannot be reproduced or improved systematically.

**Improvement:** Save every meaningful prompt version.

### Failure 4 — Model name is incomplete

**Problem:** Notes say only “Wan.”

**Risk:** The exact workflow and checkpoint cannot be identified.

**Improvement:** Record the complete model family and version.

### Failure 5 — Approved and draft assets mixed

**Problem:** Reviewers cannot identify the production selection.

**Improvement:** Use separate candidate and approved folders plus approval metadata.

---

## 22. Short quiz

1. What is the main difference between a source repository and a checkpoint?
2. Why should model files be separated from project outputs?
3. What does configuration describe?
4. Why should every candidate have a unique identity?
5. Name four settings that should be recorded as metadata.
6. Why are version numbers better than names such as `final-new`?
7. What is a shot ID used for?
8. Can a checkpoint from one model family always be used with another workflow?

---

## 23. Quiz answers

1. The repository defines workflow behavior; the checkpoint contains trained numerical parameters.
2. To prevent accidental modification and keep production assets organized.
3. How the model and workflow should be assembled and operated.
4. So experiments are not overwritten and can be compared.
5. Any four of: model, prompt, image, seed, resolution, frame count, steps, solver, guidance, audio, date.
6. Version numbers preserve order and remain unambiguous.
7. To group all assets and experiments belonging to one production shot.
8. No. Model families and their supporting configurations are workflow-specific.

---

## 24. Completion checklist

- [ ] I can distinguish source files from model weights.
- [ ] I understand the role of configuration.
- [ ] I can organize references, prompts, outputs, and reports.
- [ ] I can design a shot-based folder structure.
- [ ] I can name candidates consistently.
- [ ] I know which metadata is required for reproducibility.
- [ ] I can separate drafts from approved results.
- [ ] I understand why model-version compatibility matters.
