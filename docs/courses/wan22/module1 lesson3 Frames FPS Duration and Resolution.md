# Module 1

## Lesson 3 of 40 — Frames, FPS, Duration, and Resolution

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain frames, frame count, and FPS.
- Calculate video duration.
- Calculate required frame count.
- Distinguish resolution from aspect ratio.
- Explain why longer and larger videos require more computation.
- Choose practical draft and production settings.

---

## 2. Video as frames

A video is a sequence of still images called **frames**.

```text
Frame 1 → Frame 2 → Frame 3 → Frame 4 → ...
```

A character raising a hand may appear as:

```text
Frame 1: hand is down
Frame 2: hand begins moving
Frame 3: elbow bends
Frame 4: hand reaches shoulder height
Frame 5: hand stops
```

---

## 3. Frame count

**Frame count** is the total number of frames.

| Frame count | Example meaning |
|---:|---|
| 24 | Very short sequence |
| 48 | Twice as many frames as 24 |
| 120 | Five seconds at 24 FPS |
| 240 | Ten seconds at 24 FPS |

More frames allow longer and more detailed actions, but also increase:

- Generation time
- Memory usage
- Temporal complexity
- Identity drift risk
- Background instability risk

---

## 4. Frames per second

**FPS** means frames displayed per second.

```text
12 FPS = 12 frames each second
24 FPS = 24 frames each second
30 FPS = 30 frames each second
```

### Lower FPS

- Fewer frames per second
- Less smooth motion
- Possible stop-motion appearance

### Higher FPS

- More frames per second
- Smoother playback
- More frames required for the same duration

---

## 5. Duration formula

```text
Duration = Frame count ÷ FPS
```

Examples:

```text
120 frames ÷ 24 FPS = 5 seconds
96 frames ÷ 24 FPS = 4 seconds
120 frames ÷ 30 FPS = 4 seconds
```

The same frame count can produce different durations at different FPS values.

---

## 6. Frame-count formula

```text
Frame count = Duration × FPS
```

Examples:

```text
5 seconds × 24 FPS = 120 frames
8 seconds × 24 FPS = 192 frames
10 seconds × 30 FPS = 300 frames
```

---

## 7. Duration and storytelling

Duration is a creative decision.

This action contains many stages:

```text
Notice ball
→ turn toward ball
→ begin walking
→ approach ball
→ bend down
→ pick up ball
→ stand up
→ smile
```

Trying to place all stages into a very short clip may cause:

- Rushed action
- Missing stages
- Teleportation
- Sliding
- Unnatural body movement

A better approach is to increase duration or split the sequence into multiple shots.

---

## 8. Resolution

**Resolution** is the width and height of each frame in pixels.

```text
Width × Height
```

Examples:

```text
854 × 480
1280 × 720
1920 × 1080
```

Higher resolution can provide more detail, but increases:

- Memory use
- Processing
- Generation time
- Storage

---

## 9. Width and height

For:

```text
1280 × 720
```

- Width = 1280 pixels
- Height = 720 pixels

Total pixel positions per frame:

```text
1280 × 720 = 921,600
```

For 120 frames, this becomes a very large amount of visual data.

---

## 10. 480p and 720p

### 480p

Common widescreen example:

```text
854 × 480
```

Advantages:

- Faster drafts
- Lower memory use
- Good for testing prompts and motion

Disadvantages:

- Less facial detail
- Less small-object detail
- Less cropping flexibility

### 720p

Common widescreen example:

```text
1280 × 720
```

Advantages:

- More detail
- Better for final production
- Better textures and faces

Disadvantages:

- Higher cost
- Longer generation time
- More expensive failed experiments

---

## 11. Aspect ratio

**Aspect ratio** is the relationship between width and height.

| Aspect ratio | Typical use |
|---|---|
| 16:9 | Widescreen |
| 9:16 | Vertical mobile video |
| 1:1 | Square content |
| 4:3 | Traditional screen format |
| 2.39:1 | Very wide cinematic framing |

Remember:

```text
Aspect ratio = shape
Resolution = pixel dimensions
```

---

## 12. Aspect ratio and movement space

A wide frame provides more room for horizontal movement.

```text
┌──────────────────────────────────┐
│ Character → → →      empty space │
└──────────────────────────────────┘
```

A vertical frame may be better for standing characters or close portraits.

Choose the aspect ratio before generation because it affects composition, subject scale, and movement space.

---

## 13. Why cost increases

Video-generation cost is strongly affected by:

```text
Width × Height × Frame count
```

Increasing any dimension raises cost. Increasing all three creates a compounded increase.

More frames also create more temporal relationships that must remain consistent.

---

## 14. Draft-to-production strategy

```text
Lower-resolution draft
→ review composition and movement
→ improve prompt or source image
→ select strongest setup
→ generate final-resolution version
```

Do not use maximum resources before validating:

- Action
- Camera
- Composition
- Character count
- Movement direction
- Source-image quality

---

## 15. Important terminology

| Term | Meaning |
|---|---|
| Frame | One image in a video |
| Frame count | Total number of frames |
| FPS | Frames displayed each second |
| Duration | Total playback time |
| Resolution | Width and height in pixels |
| Aspect ratio | Relationship between width and height |
| 480p | Approximately 480 vertical pixels |
| 720p | Approximately 720 vertical pixels |
| Action space | Empty room available for movement |
| Temporal complexity | Difficulty of maintaining consistency over time |

---

## 16. Relevant generation settings

| Setting | Purpose |
|---|---|
| Frame count | Defines how many frames are generated |
| Resolution | Defines width and height |
| Aspect ratio | Defines the shape of the composition |
| Playback FPS | Determines playback duration |
| Random seed | Influences output variation |
| Sampling steps | Influences refinement cost |

Critical distinction:

```text
Frame count controls generated frames.
FPS controls how quickly they are played.
```

---

## 17. Practice calculations

1. 120 frames at 24 FPS = ? seconds
2. 6 seconds at 24 FPS = ? frames
3. 240 frames at 30 FPS = ? seconds
4. 10 seconds at 24 FPS = ? frames
5. 96 frames at 24 FPS = ? seconds
6. 4 seconds at 30 FPS = ? frames

---

## 18. Practice answers

1. 5 seconds
2. 144 frames
3. 8 seconds
4. 240 frames
5. 4 seconds
6. 120 frames

---

## 19. Production experiment

Plan three versions of:

```text
A small fox walks toward a blue watering can.
```

### Draft

- Short duration
- Lower resolution
- Simple movement
- Fixed camera

### Improved draft

- Slightly longer
- More natural walking stages
- Short pause near the watering can

### Production version

- Final duration
- Final resolution
- Approved aspect ratio
- Refined movement and camera behavior

---

## 20. Failure analysis

### Incorrect duration calculation
120 frames at 24 FPS lasts 5 seconds.

### Too many actions in too few frames
Increase duration or split the shot.

### High resolution used for every experiment
Draft at lower resolution first.

### Wrong aspect ratio for movement
Use a wider composition or reposition the subject.

### Long video causes identity drift
Shorten or divide the shot and strengthen references.

### Higher FPS misunderstood as longer duration
At the same frame count, higher FPS makes the video shorter.

---

## 21. Short quiz

1. What does FPS mean?
2. How long is 120 frames at 24 FPS?
3. How many frames are needed for eight seconds at 24 FPS?
4. What does resolution describe?
5. What does aspect ratio describe?
6. What usually happens when frame count increases?
7. What is useful for early experiments?
8. What happens when the same frames are played at higher FPS?

---

## 22. Quiz answers

1. Frames per second.
2. Five seconds.
3. 192 frames.
4. Width and height in pixels.
5. The relationship between width and height.
6. Computation and temporal complexity increase.
7. Lower-resolution drafts.
8. The video becomes shorter.

---

## 23. Completion checklist

- [ ] I understand frames, frame count, and FPS.
- [ ] I can calculate duration.
- [ ] I can calculate required frame count.
- [ ] I understand resolution.
- [ ] I understand aspect ratio.
- [ ] I know the difference between 480p and 720p.
- [ ] I understand why longer videos cost more.
- [ ] I understand why higher resolution costs more.
- [ ] I can match action complexity to duration.
- [ ] I can plan draft and production settings.
