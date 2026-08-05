# Module 3

## Lesson 10 of 40 — Spatial and Temporal Compression

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain spatial compression.
- Explain temporal compression.
- Interpret a ratio such as `16 × 16 × 4`.
- Estimate latent width, height, and temporal length.
- Explain how compression reduces cost.
- Understand how compression affects detail and motion.
- Distinguish spatial and temporal failures.
- Explain why resolution and frame count increase workload.

---

## 2. Original video dimensions

A visible video can be represented as:

```text
Width × Height × Frames
```

Example:

```text
1280 × 720 × 120
```

The VAE encoder reduces all three dimensions.

---

## 3. Spatial compression

**Spatial compression** reduces width and height.

If each spatial dimension is compressed by 16:

```text
Latent width = visible width ÷ 16
Latent height = visible height ÷ 16
```

For `1280 × 720`:

```text
1280 ÷ 16 = 80
720 ÷ 16 = 45
```

Approximate latent spatial dimensions:

```text
80 × 45
```

---

## 4. What spatial compression means

The encoder does not simply discard every sixteenth pixel.

It combines information from nearby regions into learned latent features.

```text
16 × 16 visible-pixel region
→ compressed latent information
```

The latent may preserve shape, color, texture, edges, objects, and lighting, but not every tiny detail.

---

## 5. Spatial-compression effects

More difficult to preserve:

- Fine hair
- Fingers
- Small text
- Thin lines
- Detailed fabric
- Jewelry
- Distant objects
- Small facial features

Easier to preserve:

- Character silhouette
- Large objects
- Major color regions
- Room layout
- Background geometry
- Camera composition

---

## 6. Temporal compression

**Temporal compression** reduces the time dimension.

For 120 frames with a factor of four:

```text
120 ÷ 4 = 30
```

The latent may use approximately 30 temporal positions.

Conceptually:

```text
Visible frames 1–4 → latent time position 1
Visible frames 5–8 → latent time position 2
Visible frames 9–12 → latent time position 3
```

This is a simplified explanation of learned temporal compression.

---

## 7. Why temporal compression helps

Adjacent frames often repeat most information.

If only one hand moves while the background and camera stay fixed, temporal compression can summarize the repeated structure more efficiently.

---

## 8. Temporal-compression effects

More difficult:

- Fast hand gestures
- Lip movement
- Eye blinks
- Rapid head turns
- Small facial expressions
- Thin moving objects
- Quick camera movement

Easier:

- Slow walking
- Gentle head turns
- Gradual camera movement
- Large body movement
- Slow environmental motion

---

## 9. Wan 2.2 TI2V-5B compression ratio

The course specifies:

```text
16 × 16 × 4
```

This means:

```text
Width × Height × Time
```

- Width compressed by 16
- Height compressed by 16
- Time compressed by 4

Approximate formula:

```text
W/16 × H/16 × T/4
```

---

## 10. Example calculation

Visible dimensions:

```text
1280 × 720 × 120
```

Apply compression:

```text
1280 ÷ 16 = 80
720 ÷ 16 = 45
120 ÷ 4 = 30
```

Approximate latent dimensions:

```text
80 × 45 × 30
```

---

## 11. Visible versus latent positions

Visible positions:

```text
1280 × 720 × 120
=
110,592,000
```

Latent positions:

```text
80 × 45 × 30
=
108,000
```

This simplified comparison shows the large reduction before the Transformer processes the video.

Each latent position still contains multiple learned channels.

---

## 12. Overall structural reduction

```text
16 × 16 × 4 = 1024
```

Conceptually, there is approximately one latent spatial-temporal position for every 1024 visible positions.

Actual memory reduction is not exactly 1024 because latent channels, precision, activations, and conditioning also matter.

---

## 13. 480p example

Visible:

```text
832 × 480 × 120
```

Latent:

```text
832 ÷ 16 = 52
480 ÷ 16 = 30
120 ÷ 4 = 30
```

Approximate dimensions:

```text
52 × 30 × 30
```

---

## 14. 720p example

Visible:

```text
1280 × 720 × 120
```

Latent:

```text
80 × 45 × 30
```

Approximate latent positions:

```text
80 × 45 × 30 = 108,000
```

The 720p latent workload is much larger than the 480p example.

---

## 15. Frame count and latent time

With temporal compression factor four:

```text
80 frames → 20 latent time positions
120 frames → 30 latent time positions
240 frames → 60 latent time positions
```

Doubling frame count approximately doubles latent temporal length.

This increases:

- Sequence length
- Temporal attention
- Memory
- Generation time
- Drift risk

---

## 16. Compression and video tokens

```text
Visible video
→ VAE compression
→ latent video
→ patchification
→ video tokens
```

Compression reduces latent dimensions before Transformer tokenization.

Without compression, the token sequence would be much larger.

---

## 17. Spatial versus temporal detail

### Spatial detail

- Face
- Hair
- Objects
- Texture
- Background
- Lighting

### Temporal detail

- Walking
- Speaking
- Blinking
- Turning
- Camera movement
- Object motion

A model may preserve broad motion while losing fine texture, or preserve broad structure while missing subtle motion.

---

## 18. Speaking character example

### Spatial requirements

- Stable face
- Correct mouth shape
- Consistent teeth
- Stable hair and eyes

### Temporal requirements

- Mouth changes at correct times
- Silence has little mouth movement
- Expressions follow speech
- Head movement remains natural

Subtle mouth motion is difficult under temporal compression.

---

## 19. Fast movement example

A rapidly moving hand may produce:

- Blur
- Missing intermediate pose
- Extra fingers
- Position jumps
- Duplication
- Unnatural path

The movement changes too quickly relative to the compressed temporal representation.

---

## 20. Slow movement example

A slow head turn spreads motion across more frames.

Possible benefits:

- Better facial continuity
- More natural rotation
- Less sudden deformation
- More stable hair movement

Slow controlled actions are generally easier than rapid complex actions.

---

## 21. Object permanence

The latent representation must preserve objects across compressed time positions.

A cup may:

- Change shape
- Move unexpectedly
- Disappear
- Duplicate
- Merge with a hand

if temporal consistency is weak.

---

## 22. Camera movement

Fast camera movement changes large parts of every frame.

This increases temporal difficulty.

Fixed or slowly moving cameras are easier to represent than rapid pans, tilts, zooms, rotations, or tracking movements.

---

## 23. Source-image quality

Small source-image details may weaken during encoding.

Examples:

- Tiny necklace
- Fine shirt pattern
- Small text
- Individual hair strands
- Thin glasses

Prioritize:

- Clear silhouette
- Strong shapes
- Readable colors
- Correct anatomy
- Important medium-sized features

---

## 24. Plain-language explanation

Instead of describing every pixel in every frame, a compressed summary might say:

```text
A girl stands beside a table.
She slowly reaches for a red book.
The room remains unchanged.
```

The summary preserves important structure and action but omits every hair strand, tiny shadow, and finger position.

Spatial and temporal compression work similarly.

---

## 25. Important terminology

| Term | Meaning |
|---|---|
| Spatial compression | Reducing width and height dimensions |
| Temporal compression | Reducing the time dimension |
| Compression ratio | Amount by which dimensions are reduced |
| Latent width | Width of compressed representation |
| Latent height | Height of compressed representation |
| Latent time | Temporal length of compressed representation |
| Spatial detail | Visual information within frames |
| Temporal detail | Information about change across frames |
| High-frequency detail | Small or rapidly changing information |
| Latent channel | Learned feature dimension |
| Temporal resolution | Amount of time detail represented |
| Reconstruction | Conversion back to visible video |

---

## 26. Relevant architecture concepts

| Component | Responsibility |
|---|---|
| Video VAE encoder | Compresses width, height, and time |
| Latent video | Stores compressed video information |
| Video Transformer | Processes latent representation |
| VAE decoder | Reconstructs visible frames |
| Frame count | Determines latent temporal length |
| Resolution | Determines latent spatial dimensions |
| Compression ratio | Determines reduction before generation |
| Video tokens | Represent patches of latent video |

---

## 27. Latent-dimension practice

Use `16 × 16 × 4`.

1. `1280 × 720 × 120`
2. `832 × 480 × 80`
3. `1024 × 704 × 120`
4. `768 × 768 × 96`

### Answers

1. `80 × 45 × 30`
2. `52 × 30 × 20`
3. `64 × 44 × 30`
4. `48 × 48 × 24`

---

## 28. Failure classification

| Problem | Likely category |
|---|---|
| Unreadable shirt text | Spatial detail |
| Hand jumps between positions | Temporal detail |
| Two characters appear | Broad generation structure |
| Hair texture flickers | Mixed spatial and temporal detail |
| Thin necklace disappears | Spatial detail and temporal consistency |
| Mouth misses short speech sounds | Temporal detail |
| Camera suddenly changes angle | Broad temporal or generation structure |
| Background is slightly soft | Spatial reconstruction detail |

---

## 29. Production experiment

Compare a fast and slow version of:

```text
A character slowly raises her right hand and waves once.
The camera remains stationary.
```

### Fast version risks

- Missing intermediate poses
- Blurred hand
- Finger distortion
- Sudden arm movement
- Unclear wave

### Slow version benefits

- Clearer motion stages
- Better arm continuity
- More stable hand shape
- Easier temporal representation
- Better action readability

---

## 30. Failure analysis

### Fine hair disappears
Spatial compression or reconstruction limitation.

### Fast gesture skips poses
Temporal representation difficulty.

### Higher resolution creates memory pressure
Latent width and height increase.

### Longer video causes drift
Latent temporal length increases.

### Exact small text changes
Compression, generation, and decoder limitations.

### Rapid camera pan deforms background
Large spatial changes occur too quickly.

### More frames make the action slower
This may improve motion representation but increases cost and drift risk.

---

## 31. Short quiz

1. What does spatial compression reduce?
2. What does temporal compression reduce?
3. What does `16 × 16 × 4` mean?
4. What is the latent width of 1280 with factor 16?
5. What is the latent time of 120 frames with factor 4?
6. Which is harder under temporal compression: static wall or rapid finger movement?
7. Which is harder under spatial compression: broad silhouette or small text?
8. Does latent compression eliminate computational cost?

---

## 32. Quiz answers

1. Width and height.
2. Time or frame dimension.
3. Width, height, and time compression.
4. 80.
5. 30.
6. Rapid finger movement.
7. Small text.
8. No.

---

## 33. Completion checklist

- [ ] I understand spatial compression.
- [ ] I understand temporal compression.
- [ ] I can interpret `16 × 16 × 4`.
- [ ] I can calculate latent width, height, and time.
- [ ] I understand why 720p costs more than 480p.
- [ ] I understand why more frames increase workload.
- [ ] I understand why small text and thin details are difficult.
- [ ] I understand why rapid motion is difficult.
- [ ] I understand why slow movement is often easier.
- [ ] I understand compression’s effect on speech, objects, and camera motion.
- [ ] I can distinguish spatial and temporal failures.
