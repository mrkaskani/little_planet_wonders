# Module 1

## Lesson 1 of 40 — What Video-Generation Models Do

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain what a video-generation model produces.
- Distinguish spatial consistency from temporal consistency.
- Explain how motion is represented across frames.
- Distinguish video prediction from video generation.
- Explain why generating video is harder than generating a single image.

---

## 2. Video is a sequence of frames

A digital video is a sequence of still images called **frames**.

```text
Frame 1 → Frame 2 → Frame 3 → Frame 4 → ...
```

For example, a five-second video at 24 frames per second contains:

```text
5 × 24 = 120 frames
```

A video-generation model cannot create 120 unrelated images. The frames must describe one continuous event.

For the instruction:

```text
A red fox walks from the left side of a garden to the right.
```

the model must create a progression such as:

```text
Frame 1: fox is on the left
Frame 2: fox moves slightly right
Frame 3: fox moves farther right
Frame 4: fox reaches the center
Frame 5: fox continues toward the right
```

If the frames were unrelated, the fox could change color, size, anatomy, or position between frames.

---

## 3. Architecture diagram

```text
                     Text prompt
                         │
                         ▼
               ┌──────────────────┐
               │ Video-generation │
               │      model       │
               └────────┬─────────┘
                        │
                        ▼
              Internal video representation
                        │
                        ▼
        ┌─────────┬─────────┬─────────┬─────────┐
        │ Frame 1 │ Frame 2 │ Frame 3 │ Frame 4 │
        └─────────┴─────────┴─────────┴─────────┘
              │         │         │         │
              └──── continuous time and motion ────┘
```

A video model must maintain two major kinds of consistency:

```text
Inside each frame       → spatial consistency
Between multiple frames → temporal consistency
```

---

## 4. Spatial consistency

**Spatial consistency** means that objects and their parts make sense within one frame.

For a character, the model should preserve relationships such as:

- Head connected to body
- Hands connected to arms
- Feet positioned under legs
- Eyes positioned on the face
- Character positioned correctly in the environment

A spatially inconsistent frame might contain:

- Extra limbs
- Disconnected body parts
- Objects merged together
- Incorrect perspective
- Broken background geometry

Spatial consistency also applies to buildings, furniture, vehicles, clothing, shadows, and camera perspective.

---

## 5. Temporal consistency

**Temporal consistency** means that visual information remains logically connected over time.

If a girl begins with black hair, a blue dress, and red shoes, those properties should remain stable unless the story intentionally changes them.

```text
Frame 1: black hair, blue dress, red shoes
Frame 2: black hair, blue dress, red shoes
Frame 3: black hair, blue dress, red shoes
Frame 4: black hair, blue dress, red shoes
```

Unwanted gradual change is often called **drift**.

Temporal consistency applies to:

- Character identity
- Clothing
- Background layout
- Object positions
- Lighting and shadows
- Camera direction
- Movement direction
- Object existence

### Object permanence example

```text
Frame 1: character holds a cup
Frame 2: character lowers the cup
Frame 3: cup touches the table
Frame 4: character releases the cup
Frame 5: cup remains on the table
```

A failure may cause the cup to change shape, duplicate, disappear, or reappear elsewhere.

---

## 6. Motion generation

Motion is the controlled change between frames.

It may include:

- Character movement
- Facial movement
- Lip movement
- Object movement
- Camera movement
- Environmental movement
- Lighting changes

A believable movement has intermediate stages.

```text
Hand down
→ hand begins rising
→ elbow bends
→ hand reaches shoulder height
→ hand stops
```

An unbelievable movement might teleport the hand or change the arm length.

For a prompt such as:

```text
The fox jumps over a small log.
```

the model must infer:

```text
approach
→ preparation
→ takeoff
→ airborne movement
→ landing
→ recovery
```

---

## 7. Video prediction versus video generation

### Video prediction

Video prediction starts with existing frames and predicts what happens next.

```text
Existing frames
→ predict future frames
```

### Video generation

Video generation creates a new sequence from conditions such as:

- Text
- An image
- Text plus an image
- Speech audio
- Other guidance signals

```text
Prompt or source condition
→ generate a new video
```

The main difference is:

```text
Video prediction:
Continue an observed sequence.

Video generation:
Create a sequence from instructions or conditions.
```

---

## 8. Why video generation is harder than image generation

An image model creates one visual state.

A video model must create many connected states and decide:

- How the action begins
- How quickly the subject moves
- Which body parts move
- Which objects remain still
- How the camera behaves
- What happens between start and end
- How identity and geometry remain stable

```text
Image generation:
appearance + composition

Video generation:
appearance
+ composition
+ movement
+ timing
+ continuity
+ object permanence
+ camera behavior
+ identity preservation
```

Small errors may accumulate over time. A distorted hand in one frame may become a larger object or a more serious anatomical failure later.

---

## 9. Plain-language explanation

Imagine drawing a flipbook.

For one picture, you draw the fox correctly once.

For a flipbook, you must draw the same fox repeatedly while changing its pose slightly. The background must remain stable, and the movement must look smooth when the pages are flipped.

A video-generation model performs a similar task automatically.

---

## 10. Important terminology

| Term | Meaning |
|---|---|
| Frame | One image in a video sequence |
| Spatial consistency | Correct relationships within one frame |
| Temporal consistency | Stable and logical relationships across time |
| Motion | Changes in position, shape, expression, camera, or environment |
| Drift | Unwanted gradual change across frames |
| Identity consistency | Preserving the same character’s appearance |
| Object permanence | Keeping objects present after they appear |
| Video prediction | Predicting future frames from existing frames |
| Video generation | Creating a video from conditions |
| Artifact | An unintended visual or motion error |
| Flicker | Rapid unwanted visual change between frames |

---

## 11. Relevant generation settings

| Setting | Relevance |
|---|---|
| Frame count | Determines how many frames are generated |
| Resolution | Controls spatial dimensions |
| Prompt | Describes subjects, actions, camera, lighting, and style |
| Source image | Provides a visual starting condition |
| Speech audio | Provides timing and performance guidance |
| Random seed | Influences composition and movement variation |

Remember:

```text
More frames
= more temporal information
= more motion opportunities
= more opportunities for inconsistency
```

---

## 12. Practice activity

Open a short video and move through it one frame at a time.

Record:

```text
Subject:
Action:
What remains spatially stable:
What changes between adjacent frames:
What remains temporally stable:
Camera movement:
Possible generation difficulties:
```

---

## 13. Expected result

You should notice that adjacent frames change only slightly, while identity, clothing, background, and camera composition remain mostly stable.

A video model must reproduce both the changes and the stability.

---

## 14. Failure analysis

### Flickering appearance
Temporal-consistency failure.

### Extra limbs
Spatial and temporal failure.

### Teleporting subject
Motion-trajectory failure.

### Changing background
Temporal-consistency failure.

### Sliding instead of walking
Motion and physical-contact failure.

### Unrequested camera movement
Camera-conditioning or prompt-interpretation failure.

---

## 15. Short quiz

1. What is a frame?
2. What does spatial consistency describe?
3. What does temporal consistency describe?
4. A shirt changes color unintentionally. What type of problem is this?
5. What is the difference between video prediction and video generation?
6. Why is video generation harder than image generation?

---

## 16. Quiz answers

1. One image in a video sequence.
2. Correct relationships inside one frame.
3. Stability and logical change across frames.
4. Temporal drift.
5. Prediction continues existing frames; generation creates a sequence from conditions.
6. Video must maintain motion, timing, identity, and continuity across many connected frames.

---

## 17. Completion checklist

- [ ] I can explain what a frame is.
- [ ] I can explain spatial consistency.
- [ ] I can explain temporal consistency.
- [ ] I can explain motion generation.
- [ ] I can explain drift and object permanence.
- [ ] I can distinguish video prediction from video generation.
- [ ] I can explain why video generation is difficult.
- [ ] I can identify common video-generation failures.
