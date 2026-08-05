# Module 8

## Lesson 28 of 40 — I2V Conditioning

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain how image conditioning changes video generation.
- Describe what the source image controls strongly.
- Describe what the source image does not perfectly guarantee.
- Trace the I2V conditioning pipeline.
- Distinguish first-frame control from future-motion control.
- Identify conditioning, generation, and reconstruction failures.

---

## 2. Official model covered

The course identifies the dedicated image-driven production model as:

```text
Wan 2.2 I2V-A14B
```

I2V begins with an approved image and generates movement from that visual condition.

---

## 3. Core I2V pipeline

```text
Input image
+
motion prompt
+
noisy future latent frames
→ conditioned video generation
→ generated latent video
→ VAE decoding
→ visible video
```

The image provides visual structure.

The prompt describes change.

The model generates future temporal content.

---

## 4. First-frame condition

The source image strongly establishes the opening visual state.

It can control:

- Character appearance
- Face
- Hair
- Clothing
- Starting pose
- Background
- Object placement
- Camera framing
- Color palette
- Initial lighting

This gives I2V stronger initial visual control than T2V.

---

## 5. What the image does not control exactly

The image does not contain complete information about future frames.

It does not perfectly specify:

- Exact motion path
- Exact speed
- Exact ending pose
- Future facial angles
- Hidden body regions
- Object behavior after interaction
- Identity throughout the full clip

The model must infer these from learned patterns and the motion prompt.

---

## 6. Image encoding

The source image is converted into an internal visual condition.

Conceptually:

```text
Visible source image
→ visual encoding
→ latent or embedding condition
→ video generator
```

Important visual traits must survive encoding.

Tiny or malformed details may be weakened or amplified.

---

## 7. Noisy future latent frames

The opening image provides known visual information, but future frames begin as uncertain latent states.

Conceptually:

```text
Known first-frame condition
+
noisy future representation
→ generated temporal continuation
```

This is why future identity is guided but not guaranteed.

---

## 8. Prompt responsibility

In I2V, the prompt should focus on:

- What moves
- How it moves
- How fast it moves
- Emotional change
- Camera behavior
- What remains unchanged

The prompt should not unnecessarily redescribe every visible detail already present in the image.

---

## 9. Strong image control

The source image strongly influences:

- Initial composition
- Subject colors
- Wardrobe
- Location
- Starting camera position
- Object arrangement
- Initial silhouette

This makes I2V appropriate for approved keyframes and recurring characters.

---

## 10. Limited future control

Future generation can still introduce:

- Face drift
- Hair changes
- Clothing changes
- Background warping
- Object disappearance
- Wrong ending pose
- Unrequested camera movement

The further the clip moves from the source state, the more new information must be generated.

---

## 11. Hidden-information problem

A single image shows only one viewpoint.

If a character turns around, the model must invent:

- Side of the face
- Back of the head
- Hidden clothing
- Occluded body parts
- Background regions revealed by movement

An image cannot directly guarantee details that are not visible.

---

## 12. Motion-space requirement

The source composition should leave room for movement.

Example:

```text
Character must walk right
→ character should begin left of center
```

Insufficient movement space may cause:

- Character compression
- Background warping
- Unwanted camera movement
- Weak or nearly static action

---

## 13. Image and prompt agreement

The source image and prompt should support the same action.

Conflict example:

- Image: tightly cropped face
- Prompt: character walks across the room

Conflict example:

- Image: character facing left at the right edge
- Prompt: character walks farther right

Conflict example:

- Image: seated character
- Prompt: begins running immediately

Choose an image whose pose and composition make the requested action plausible.

---

## 14. Camera conditioning

The image strongly establishes the starting camera angle.

The prompt can request:

- Fixed camera
- Slow push-in
- Gentle pan
- Small tracking motion

Large camera changes require the model to invent unseen environment regions and may reduce stability.

---

## 15. Identity conditioning

Identity is supported through:

- Face shape
- Hair
- Clothing
- Color palette
- Silhouette
- Distinctive features

Identity is easier to preserve when:

- Movement is slow
- Head rotation is moderate
- Shot is short
- Camera is stable
- Source image is clear
- Important features are visible

---

## 16. Object permanence

If the source image contains a prop, the model must maintain it through time.

Possible failures:

- Prop changes shape
- Prop moves without cause
- Prop disappears
- Prop duplicates
- Hand merges with prop

Simple object relationships and slow interaction improve the chance of consistency.

---

## 17. Background conditioning

A source image can establish an exact background more strongly than text.

However, background stability can still fail through:

- Texture shimmer
- Geometry warping
- New objects
- Lighting changes
- Camera drift

A clean, stable, moderately detailed background is generally easier than a crowded one.

---

## 18. I2V versus T2V

| Question | T2V | I2V |
|---|---|---|
| Approved first image required | No | Yes |
| Initial identity control | Lower | Stronger |
| Initial composition control | Lower | Stronger |
| Creative freedom | Higher | More constrained |
| Exact future motion guaranteed | No | No |
| Suitable for recurring character | Limited | Better suited |

---

## 19. Pipeline failure map

| Failure | Likely area |
|---|---|
| Defect already in first frame | Source image |
| Wrong motion direction | Prompt or temporal generation |
| Face changes during turn | Identity and temporal generation |
| Stable structure but soft texture | Decoder or resolution |
| Background moves with fixed camera | Temporal consistency |
| Video is almost static | Motion prompt or conditioning conflict |

---

## 20. Plain-language explanation

I2V is like giving an animator the exact first drawing of a scene.

The animator knows how the character and environment should begin.

But the animator must still invent every later pose, hidden angle, and movement stage.

The first drawing improves consistency but does not fully define the complete animation.

---

## 21. Important terminology

| Term | Meaning |
|---|---|
| I2V | Image-to-Video |
| Source image | Approved visual starting condition |
| Image conditioning | Using image information to guide generation |
| First-frame control | Strong influence over the opening visual state |
| Future latent frames | Uncertain internal representation of later frames |
| Hidden information | Visual content not shown in the source image |
| Motion space | Empty composition area available for movement |
| Invariant | Property intended to remain unchanged |
| Identity drift | Unwanted change in character appearance |
| Object permanence | Keeping an object stable and present over time |

---

## 22. Relevant settings

- I2V task
- I2V checkpoint
- Prompt
- Source image
- Resolution
- Frame count
- Sampling steps
- Solver
- Guidance
- Shift
- Seed
- Output destination
- Memory options

The source-image version must be recorded along with the generation settings.

---

## 23. Practical activity

Analyze this source-image plan:

```text
Character stands at the right edge of a garden image, facing right.
The shot requires her to walk toward a red ball farther to the right.
```

Identify the conditioning problems and redesign the first frame.

---

## 24. Expected result

Problems:

- No movement space on the right
- Character already faces out of frame
- Ball may be outside the visible composition
- Model may move the camera or warp the scene

Improved first frame:

- Character begins left of center
- Character faces or turns toward the right
- Red ball is visible with space between subject and target
- Full body is visible if walking is required
- Camera framing remains stable

---

## 25. Failure analysis

### Failure 1 — Source image has malformed anatomy

**Result:** The defect remains or worsens.

**Improvement:** Correct the source before generation.

### Failure 2 — Image and prompt request incompatible poses

**Result:** Sudden deformation or static output.

**Improvement:** Choose a source pose closer to the intended action.

### Failure 3 — Large head turn changes identity

**Cause:** Hidden facial angles must be invented.

**Improvement:** Reduce rotation or provide a more suitable reference.

### Failure 4 — Background warps during camera movement

**Cause:** New environment regions must be generated.

**Improvement:** Use a fixed or smaller camera move.

### Failure 5 — Image assumed to guarantee ending pose

**Problem:** The source defines the start, not an exact final state.

---

## 26. Short quiz

1. What does the source image control strongly?
2. What must still be generated after the source image is supplied?
3. Why can hidden character details change?
4. What is motion space?
5. Why should image and prompt agree?
6. Does I2V guarantee exact ending pose?
7. Why can object permanence fail?
8. When is I2V preferable to T2V?

---

## 27. Quiz answers

1. Initial appearance, composition, pose, colors, background, and camera position.
2. Future motion and later frames.
3. The image does not show every angle or occluded region.
4. Empty composition area available for the intended movement.
5. Conflicting conditions make plausible temporal generation difficult.
6. No.
7. Future frames must maintain the object through generated motion and interactions.
8. When approved identity, composition, wardrobe, or location control is needed.

---

## 28. Completion checklist

- [ ] I can trace the I2V conditioning pipeline.
- [ ] I understand first-frame versus future-frame control.
- [ ] I know what the image strongly controls.
- [ ] I know what the image cannot guarantee.
- [ ] I understand hidden-information and motion-space problems.
- [ ] I can identify image–prompt conflicts.
- [ ] I can diagnose source, generation, and decoder failures.
- [ ] I know when I2V is preferable to T2V.
