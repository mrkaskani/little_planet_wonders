# Module 9

## Lesson 33 of 40 — TI2V-5B Architecture and Efficiency

**Study time:** approximately 25 minutes  
**Practice time:** approximately 20 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- explain what the course means by a dense 5B model;
- distinguish dense processing from Wan’s A14B expert specialization;
- explain how a high-compression VAE reduces latent workload;
- connect resolution, frame count, token count, and memory use;
- describe why TI2V-5B is useful for 720p and 24 FPS workflows as stated in the course source;
- evaluate quality-versus-efficiency trade-offs;
- plan a drafting workflow that uses computational resources efficiently.

---

## 2. Course-defined architecture summary

The course describes TI2V-5B using these properties:

- approximately 5B dense model family;
- one model supporting text and image modes;
- high-compression video VAE;
- 720p generation support;
- 24 FPS support;
- lower memory requirements than A14B models;
- a quality-versus-efficiency trade-off.

These properties explain its role as an efficient drafting and experimentation model.

---

## 3. What “5B” communicates

“5B” refers to a model scale of roughly five billion learned parameters in the course naming.

Parameters store learned transformation behavior.

They contribute to the model’s ability to represent:

- visual patterns;
- motion patterns;
- prompt relationships;
- spatial and temporal structure;
- image conditioning;
- denoising behavior.

Parameter count alone does not determine output quality. Training data, architecture, latent representation, conditioning, and sampling also matter.

---

## 4. What “dense” means

A dense model uses its main parameter pathway consistently rather than activating separate high-noise and low-noise expert parameter sets as described for the A14B family.

Conceptually:

```text
TI2V-5B dense path:
all generation stages
→ shared dense model pathway
```

Compared with the course’s A14B description:

```text
high-noise stage → high-noise expert
low-noise stage  → low-noise expert
```

Dense does not mean that every parameter has equal influence at every moment. Timestep conditioning still changes behavior. It means the architecture is not divided into the same two expert pathways described for A14B.

---

## 5. Dense-model strengths

A dense model can provide:

- simpler execution structure;
- predictable active model size;
- one shared representation across the trajectory;
- reduced total parameter scale compared with A14B;
- easier use as a unified drafting model.

The main production benefit is not merely “smaller is faster.” It is that a smaller dense model may fit environments where a larger expert model is impractical.

---

## 6. High-compression VAE

The course states that TI2V-5B uses a VAE with a documented compression ratio of:

```text
16 × 16 × 4
```

This means compression across:

- width by 16;
- height by 16;
- time by 4.

For a visible video of:

```text
1280 × 720 × 120 frames
```

an approximate latent structure is:

```text
80 × 45 × 30 temporal positions
```

The model operates on a much smaller latent grid than the original pixel video.

---

## 7. Why high compression improves efficiency

Compression reduces:

- spatial positions;
- temporal positions;
- number of patches;
- Transformer sequence length;
- attention workload;
- activation memory;
- sampling cost.

Conceptually:

```text
more compression
→ fewer latent elements
→ fewer video tokens
→ lower model workload
```

However, stronger compression also increases the difficulty of preserving:

- small text;
- fingers;
- hair strands;
- fine fabric patterns;
- rapid lip movement;
- subtle facial changes;
- thin moving objects.

Efficiency and detail preservation are connected trade-offs.

---

## 8. 720p and 24 FPS in production terms

The course source identifies 720p and 24 FPS support for TI2V-5B.

These terms describe different dimensions:

- 720p concerns spatial resolution;
- 24 FPS concerns playback rate.

A five-second 24 FPS result requires approximately:

```text
5 × 24 = 120 visible frames
```

With temporal compression by four, the latent time dimension is approximately 30 positions before later patchification.

This helps explain how the model can work with a production-friendly visible format while operating on a compressed representation.

---

## 9. Resolution cost

Increasing width and height increases the latent spatial grid.

Compare approximate latent dimensions under 16× spatial compression:

| Visible size | Approximate latent size |
|---|---|
| 832 × 480 | 52 × 30 |
| 1280 × 720 | 80 × 45 |

For the same temporal length, 720p produces more than twice the latent spatial positions of the 480p example.

This affects:

- attention computation;
- activation memory;
- generation time;
- VAE decoding cost.

---

## 10. Frame-count cost

Increasing frame count increases latent temporal length.

With temporal compression by four:

| Visible frames | Approximate latent time |
|---:|---:|
| 80 | 20 |
| 120 | 30 |
| 240 | 60 |

A longer sequence creates more temporal relationships to model.

This can increase:

- memory use;
- attention cost;
- identity-drift risk;
- background-drift risk;
- object-permanence difficulty.

---

## 11. Why TI2V requires less memory than A14B

The course’s explanation rests on multiple factors:

1. smaller parameter scale;
2. dense 5B architecture rather than larger A14B total capacity;
3. high-compression VAE;
4. reduced latent sequence compared with less compressed representations.

Memory is still required for:

- model parameters;
- temporary activations;
- attention operations;
- text conditioning;
- source-image encoding;
- VAE decoding;
- sampling state.

A lower-memory model is not a low-cost model in absolute terms. Video generation remains demanding.

---

## 12. Quality-versus-efficiency trade-off

TI2V-5B may be a strong choice when the primary question is:

> Can this shot idea, prompt, motion, and composition work?

A14B may be a stronger choice when the primary question is:

> Can this approved shot achieve the best available detail and production quality within our workflow?

Potential TI2V trade-offs include:

- less fine detail;
- weaker complex motion;
- reduced facial stability;
- weaker identity preservation;
- simpler texture;
- lower tolerance for crowded scenes.

The correct conclusion is not that TI2V is “bad quality.” Its value is measured against speed, memory, iteration count, and production stage.

---

## 13. Efficient drafting pipeline

```text
Shot idea
→ low-cost TI2V draft
→ evaluate structure and motion
→ refine prompt or source image
→ compare several seeds
→ approve creative setup
→ generate production candidate
```

During drafting, prioritize:

- subject count;
- action direction;
- camera framing;
- movement readability;
- duration;
- source-image suitability.

Do not reject a useful draft only because hair texture is not final. Likewise, do not approve a structurally wrong draft because one frame is attractive.

---

## 14. Architecture responsibility map

```text
Input text/image
        │
        ▼
Condition encoding
        │
        ▼
Compressed latent video
        │
        ▼
Dense 5B Transformer processing
        │
        ▼
Sampled latent result
        │
        ▼
VAE reconstruction
        │
        ▼
720p-visible output
```

Use the map to classify failures:

- wrong scene structure → generation;
- weak source identity → input or image conditioning;
- fine shimmer → latent detail or VAE reconstruction;
- long-shot drift → temporal generation;
- memory pressure → resolution, frame count, activations, model scale.

---

## 15. Practical efficiency experiment

Plan three drafts of one shot:

```text
One character slowly opens a red book on a wooden table.
The camera remains fixed.
```

### Run A

Lower resolution and short duration.

Purpose: validate composition and action direction.

### Run B

720p with the same short action.

Purpose: observe spatial-cost and detail changes.

### Run C

720p with longer duration.

Purpose: observe temporal cost and drift.

Record:

- generation time;
- peak memory if available;
- latent complexity estimate;
- action success;
- face and hand quality;
- background stability;
- usefulness for production.

---

## 16. Expected result

Run A should be the cheapest and most useful for early structural feedback.

Run B may improve visible detail but cost more.

Run C may provide more time for the action but increase temporal workload and drift risk.

The best production decision may be to keep the action short rather than simply increasing duration.

---

## 17. Failure analysis

### Failure: 720p output is still structurally wrong

Higher resolution adds detail capacity, not correct semantics.

### Failure: fast lips or fingers look unstable

High temporal and spatial compression makes subtle rapid detail difficult.

### Failure: memory use rises sharply with duration

Longer videos increase latent time and token relationships.

### Failure: TI2V draft looks weaker than A14B

This may be the expected quality-versus-efficiency trade-off. Judge whether the draft answered the production question.

### Failure: team uses production quality for every prompt test

This wastes resources before the creative setup is validated.

---

## 18. Plain-language explanation

TI2V-5B is like making a detailed storyboard with a smaller, faster production team. The team can explore both new scenes and image-based motion without using the largest available crew for every attempt.

The high-compression VAE is like summarizing many pixels and frames into a smaller set of production notes. This saves work, but extremely small visual details can be harder to preserve.

---

## 19. Important terminology

| Term | Meaning |
|---|---|
| Dense model | Shared main parameter pathway across generation stages |
| 5B | Approximate parameter-scale label in the model name |
| High-compression VAE | Encoder/decoder using strong spatial and temporal compression |
| Latent workload | Amount of compressed video data processed |
| Active parameters | Parameters involved during a generation stage |
| Activation memory | Temporary intermediate data created during processing |
| Drafting workflow | Low-cost iteration before final production |
| Efficiency trade-off | Exchanging some quality potential for lower cost or faster iteration |

---

## 20. Short quiz

1. What does dense mean in this lesson?
2. What are the three dimensions in the 16 × 16 × 4 ratio?
3. Why does compression reduce attention cost?
4. Does 720p describe FPS?
5. How many frames are approximately required for five seconds at 24 FPS?
6. Why can longer duration increase drift?
7. Why is TI2V useful before A14B production?
8. Does lower memory mean video generation is inexpensive?

---

## 21. Quiz answers

1. The main model pathway is shared rather than divided into the A14B high-noise and low-noise experts described in the course.
2. Width, height, and time.
3. It reduces latent positions and therefore reduces tokens and token relationships.
4. No. It describes vertical resolution.
5. 120 frames.
6. The model must preserve identity, objects, and background across a longer temporal sequence.
7. It can test prompts, composition, seeds, and motion at lower cost.
8. No. Video generation still requires substantial parameters, activations, attention, and decoding.

---

## 22. Completion checklist

- [ ] I can explain dense 5B architecture conceptually.
- [ ] I can distinguish TI2V from A14B expert specialization.
- [ ] I can calculate approximate latent dimensions.
- [ ] I understand 720p versus 24 FPS.
- [ ] I can explain resolution and frame-count cost.
- [ ] I can describe the quality-efficiency trade-off.
- [ ] I can plan an efficient drafting pipeline.
- [ ] I can evaluate whether a draft answered the correct production question.
