# Module 6

## Lesson 23 of 40 — Memory and Computational Cost

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Distinguish model-parameter memory from activation memory.
- Explain attention, VAE, and text-encoder memory costs.
- Predict how resolution, frame count, and batch size affect memory.
- Explain CPU offloading and reduced precision.
- Identify the difference between peak memory and total generation time.
- Design a practical draft-to-production resource strategy.

---

## 2. Why video generation is memory-intensive

Video generation combines several expensive factors:

- Large model parameters
- Many latent video tokens
- Spatial and temporal attention
- Multiple sampling steps
- VAE encoding and decoding
- Text, image, or audio conditioning
- Temporary intermediate activations

The model does not store only the final video.

It must maintain working data during generation.

---

## 3. Main memory categories

```text
Total working memory
≈
model parameters
+
activations
+
attention workspace
+
VAE workspace
+
conditioning models
+
temporary buffers
+
output data
```

The exact total depends on implementation and hardware.

---

## 4. Model-parameter memory

Model parameters are the learned numerical values stored inside the network.

Larger model families generally require more memory for their parameters.

Parameter memory depends on:

- Number of parameters
- Numerical precision
- Which components are loaded at the same time
- Whether inactive components are offloaded

A14B model families contain greater total capacity than the dense 5B model described in the course.

---

## 5. Precision and parameter memory

A parameter stored using fewer bits requires less memory.

Conceptually:

```text
Higher precision
→ more bytes per value

Lower precision
→ fewer bytes per value
```

Reduced precision may also improve processing speed on compatible hardware.

However, not every model component tolerates every precision equally well.

---

## 6. Activation memory

Activations are temporary values produced while the model processes the current latent video.

They depend strongly on:

- Token count
- Model width
- Number of layers
- Batch size
- Conditioning
- Attention implementation

Activation memory can be large even when parameter memory remains fixed.

This explains why a model may load successfully but fail when generation begins at a large resolution or frame count.

---

## 7. Attention memory

Attention relates video tokens across space and time.

More tokens create more relationships to process.

Token count grows with:

- Latent width
- Latent height
- Latent time
- Smaller patch sizes
- Batch size

Conceptually:

```text
higher resolution
+
more frames
→ more tokens
→ greater attention cost
```

Some attention methods reduce memory growth, but sequence length remains a major cost driver.

---

## 8. Resolution cost

Increasing width increases latent width.

Increasing height increases latent height.

Increasing both produces a multiplied effect.

Example:

```text
latent spatial positions
=
latent width × latent height
```

A 720p workflow can contain more than twice the latent spatial positions of a lower-resolution draft, depending on the exact dimensions.

---

## 9. Frame-count cost

More visible frames produce more latent temporal positions.

With temporal compression by four:

```text
120 frames → approximately 30 latent time positions
240 frames → approximately 60 latent time positions
```

Doubling frame count approximately doubles latent temporal length.

This increases:

- Activation memory
- Attention work
- Generation time
- Consistency difficulty

---

## 10. Batch-size cost

Batch size is the number of samples processed together.

Increasing batch size can improve throughput on large hardware, but memory use often rises substantially because each sample needs its own:

- Latent state
- Activations
- Attention data
- Output buffers

For limited hardware, generating candidates sequentially is often more practical than increasing batch size.

---

## 11. VAE memory

The video VAE is responsible for encoding and decoding.

VAE memory depends on:

- Output resolution
- Frame count
- Internal feature maps
- Temporal processing
- Precision
- Whether encoding and decoding are chunked

Decoding a high-resolution long video can create a separate memory peak after denoising has completed.

---

## 12. Text-encoder memory

The text encoder converts the prompt into embeddings.

Its memory use is usually smaller than the main video model but can still matter when GPU memory is limited.

Moving it to CPU can free GPU memory after or during prompt processing.

Possible trade-off:

- Lower GPU-memory pressure
- Slower prompt processing and transfer

---

## 13. Image and audio conditioning memory

I2V and S2V include additional conditions.

These may require:

- Image encoding
- Audio feature extraction
- Pose processing
- Additional embeddings
- Conditioning buffers

The total workflow cost is therefore not determined only by the main model size.

---

## 14. Peak memory versus average memory

**Peak memory** is the highest memory usage reached during the workflow.

Different stages may create different peaks:

1. Model loading
2. Prompt encoding
3. Image or audio encoding
4. Denoising
5. VAE decoding
6. Output assembly

A system succeeds only if it can handle the highest stage, not merely the average.

---

## 15. GPU memory versus system memory

### GPU memory

Used for:

- Active model components
- Activations
- Attention
- Latent video
- GPU-side VAE work

### System memory

Used for:

- Offloaded model components
- Input assets
- Intermediate CPU buffers
- Decoded frames
- Output assembly

Offloading reduces GPU pressure by increasing system-memory use and data transfer.

---

## 16. CPU offloading

CPU offloading moves inactive components out of GPU memory.

Conceptually:

```text
Component needed now
→ GPU

Component temporarily inactive
→ CPU memory
```

Possible advantage:

- Larger model or video fits within GPU memory

Possible disadvantages:

- Transfer latency
- Lower generation speed
- Greater system-memory requirement
- More complex performance behavior

---

## 17. Reduced precision

Reduced precision lowers memory per model value and may lower activation memory.

Potential benefits:

- Lower memory usage
- Higher processing throughput
- Larger feasible video dimensions

Potential risks:

- Numerical instability
- Unsupported operations
- Changed quality
- Component-specific compatibility problems

Every precision strategy should be tested on the intended workflow.

---

## 18. Memory-saving changes and their trade-offs

| Change | Memory effect | Possible trade-off |
|---|---|---|
| Lower resolution | Strong reduction | Less fine detail |
| Fewer frames | Strong reduction | Shorter action or less temporal room |
| Smaller batch | Strong reduction | Lower throughput |
| Reduced precision | Parameter and activation reduction | Compatibility or quality risk |
| CPU offloading | Lower GPU memory | Slower generation |
| Text encoder on CPU | Frees GPU memory | Prompt-processing overhead |
| Smaller model | Lower parameter memory | Potentially lower quality or capacity |

---

## 19. Computational cost versus memory cost

Memory and compute are related but not identical.

A configuration may:

- Fit in memory but run very slowly
- Use little GPU memory because of offloading but spend time transferring data
- Use reduced precision and run faster
- Increase steps without greatly increasing peak memory but substantially increase total time

Always measure both:

- Peak memory
- Generation time

---

## 20. Sampling-step cost

Increasing sampling steps normally increases the number of model evaluations.

Conceptually:

```text
more steps
→ more repeated processing
→ longer generation time
```

Peak memory may remain similar because the same latent shape is processed repeatedly.

Therefore, steps often affect compute time more strongly than latent memory size.

---

## 21. Model-size cost

A larger model may improve capacity and final quality, but it also increases:

- Parameter memory
- Compute per step
- Loading time
- Offloading cost
- Hardware requirements

This is why the course positions TI2V-5B as useful for rapid drafting and the A14B models as stronger production options.

---

## 22. Draft-to-production strategy

```text
Draft stage
→ lower resolution
→ shorter duration
→ smaller model when appropriate
→ moderate steps
→ several seeds

Selection stage
→ approve composition and motion

Production stage
→ final model
→ final resolution
→ validated frame count
→ tested sampling settings
```

This prevents expensive high-quality generation of structurally unusable shots.

---

## 23. Resource estimation order

Before generation, evaluate:

1. Model family
2. Resolution
3. Frame count
4. Batch size
5. Conditioning requirements
6. Sampling steps
7. Precision
8. Offloading

The first four usually have the clearest effect on memory demand.

---

## 24. Which increase costs more?

The answer depends on the baseline dimensions.

### Increasing width only

Raises latent width and token count.

### Increasing height only

Raises latent height and token count.

### Increasing width and height

Multiplies spatial growth and can be especially expensive.

### Increasing frame count

Raises temporal length and attention work.

### Increasing batch size

Replicates most per-sample working data.

---

## 25. Plain-language explanation

Imagine a workshop producing animated books.

Memory is the size of the worktable.

Compute is the amount of work required.

A larger book, more pages, and more copies need a larger table and more labor.

Offloading moves some materials to another room. This frees table space but workers spend time carrying materials back and forth.

---

## 26. Important terminology

| Term | Meaning |
|---|---|
| Parameter memory | Memory storing learned model values |
| Activation memory | Temporary working values during processing |
| Attention memory | Workspace used to relate tokens |
| Peak memory | Highest memory usage during the workflow |
| Batch size | Number of samples processed together |
| Offloading | Moving components from GPU to CPU memory |
| Precision | Numerical size and accuracy of stored values |
| Throughput | Amount of work completed per unit time |
| Latency | Time required for one generation |
| Memory pressure | Demand approaching available memory capacity |
| Out-of-memory failure | Workflow stops because required memory is unavailable |

---

## 27. Practical activity

Rank these changes from likely lower to higher memory impact for the same baseline shot:

- Increase sampling steps
- Double frame count
- Increase both width and height
- Double batch size
- Move the text encoder to CPU

Then explain which changes mostly affect generation time and which affect peak memory.

---

## 28. Expected result

A strong answer should recognize:

- More steps primarily increase total computation.
- More frames increase latent temporal memory and compute.
- Increasing both width and height strongly increases spatial token count.
- Doubling batch size duplicates much per-sample working data.
- Moving the text encoder to CPU reduces GPU memory but may add overhead.

Exact rankings depend on implementation and starting dimensions.

---

## 29. Failure analysis

### Failure 1 — Model loads but generation fails

**Likely cause:** Parameters fit, but activations or attention exceed memory.

### Failure 2 — Denoising finishes but decoding fails

**Likely cause:** VAE decoding creates a separate peak.

### Failure 3 — Offloading makes generation extremely slow

**Cause:** Frequent CPU–GPU transfers.

### Failure 4 — Increasing steps does not cause the expected memory increase

**Explanation:** Steps repeat computation over similar working shapes; they often increase time more than peak memory.

### Failure 5 — Batch generation fails while single generation succeeds

**Cause:** Batch size replicates per-sample states and activations.

---

## 30. Short quiz

1. What is parameter memory?
2. What is activation memory?
3. Why does higher resolution increase attention cost?
4. Why does frame count affect temporal memory?
5. What is peak memory?
6. What is the primary benefit of CPU offloading?
7. What is a major cost of offloading?
8. Do more sampling steps always greatly increase peak memory?

---

## 31. Quiz answers

1. Memory storing the model’s learned numerical values.
2. Temporary working memory produced while processing a sample.
3. It creates more latent spatial positions and tokens.
4. More frames create more latent temporal positions.
5. The highest memory usage reached during any workflow stage.
6. Reducing GPU-memory demand.
7. CPU–GPU transfer overhead and slower generation.
8. Not necessarily; they often increase total compute time more than peak memory.

---

## 32. Completion checklist

- [ ] I can distinguish parameters, activations, and attention memory.
- [ ] I understand VAE and text-encoder memory.
- [ ] I know why resolution and frame count are expensive.
- [ ] I understand batch-size scaling.
- [ ] I can explain peak memory.
- [ ] I understand CPU offloading and reduced precision.
- [ ] I can distinguish memory cost from compute time.
- [ ] I can design a resource-efficient draft-to-production workflow.
