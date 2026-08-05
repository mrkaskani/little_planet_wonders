# Module 8

## Lesson 29 of 40 — Preparing an I2V Source Image

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Select or create a suitable I2V source image.
- Evaluate silhouette, anatomy, background, movement space, aspect ratio, and subject clarity.
- Remove conflicting subjects, text, and collage-like elements.
- Match framing and pose to the intended action.
- Build a pre-generation image review checklist.
- Explain why source-image defects often continue into video.

---

## 2. The source image is the visual foundation

In I2V, the source image defines the opening visual state.

The model will use it to infer:

- Character identity
- Starting pose
- Scene geometry
- Object relationships
- Camera position
- Color palette
- Lighting

A weak source image creates a weak condition before video generation begins.

---

## 3. Clear silhouette

A **silhouette** is the outer shape of a subject.

A clear silhouette helps the model distinguish:

- Head
- Torso
- Arms
- Legs
- Props
- Background

Weak silhouette examples:

- Arms merge with body
- Hair merges with dark background
- Hand overlaps face
- Legs overlap each other
- Prop merges with clothing

Separate important shapes visually.

---

## 4. Correct anatomy

Review the image before generation for:

- Correct number of fingers
- Correct arm and leg connections
- Symmetrical eyes where intended
- Natural joint positions
- Plausible body proportions
- Clear hand–object relationships

The model may preserve or amplify anatomical errors.

Do not expect motion generation to repair a defective first frame reliably.

---

## 5. Stable background

A useful I2V background should have:

- Clear geometry
- Consistent perspective
- Readable large shapes
- Limited unnecessary clutter
- No accidental duplicate objects
- No severe visual noise

Crowded, highly repetitive, or distorted backgrounds increase the risk of temporal warping.

---

## 6. Movement space

Movement space is the empty area available in the direction of action.

Examples:

### Walking right

Place the subject left of center.

### Reaching toward an object

Leave visible distance between hand and object.

### Camera push-in

Ensure the subject has enough framing margin.

### Head turn

Leave space in the direction of gaze.

---

## 7. Correct aspect ratio

The source image should match the intended output shape.

Changing aspect ratio after source preparation can:

- Crop the subject
- Change composition
- Remove movement space
- Alter subject scale
- Reveal unintended borders

Plan horizontal, vertical, or square framing before generation.

---

## 8. Framing must match the action

### Full-body movement

Use a frame that shows:

- Feet
- Ground contact
- Movement direction
- Surrounding action space

### Hand action

Use framing that keeps:

- Hand
- Arm
- Target object

clearly visible.

### Facial performance

Use a closer frame with:

- Clear face
- Clean hair boundary
- Visible eyes and mouth

---

## 9. Starting pose

The source pose should be close to the first stage of the requested motion.

Good example:

- Character standing before a slow walk

Poor example:

- Character seated while the prompt requests immediate running

A large pose discontinuity increases deformation risk.

---

## 10. No collage

A collage contains multiple separate images or views inside one frame.

Examples:

- Front and side character views together
- Character sheet with several poses
- Split-screen reference
- Mood board containing unrelated scenes

A generation source image should usually contain one coherent scene.

Collages can cause:

- Multiple characters
- Split-screen artifacts
- Mixed poses
- Confused backgrounds

---

## 11. No unwanted text

Remove:

- Watermarks
- Captions
- Labels
- Interface elements
- Signatures
- Prompt text

Text may:

- Distort during motion
- Become embedded into the generated scene
- Flicker
- Distract the model

Critical text should be added during editing.

---

## 12. No conflicting subjects

The source image should clearly identify the main subject.

Avoid:

- Extra people in the background
- Reflections that resemble another character
- Posters containing faces
- Statues resembling people
- Duplicate animals

Conflicting subjects can create wrong subject counts or attention mixing.

---

## 13. Identity readability

Important character traits should be visible and medium-sized.

Prioritize:

- Face
- Hair shape and color
- Clothing color
- Silhouette
- Major accessories

Do not depend on:

- Tiny jewelry
- Small logos
- Fine fabric text
- Individual hair strands

These may not survive compression and temporal generation.

---

## 14. Lighting quality

The source should use coherent lighting.

Check:

- One understandable primary direction
- No conflicting shadows
- Face is readable
- Important objects are visible
- No extreme overexposure
- No crushed dark details

The generated video will attempt to continue the lighting pattern.

---

## 15. Background–subject separation

Separate the subject from the background through:

- Color contrast
- Value contrast
- Depth
- Clean boundaries
- Lighting

Poor separation can cause body parts or clothing to merge into the environment during motion.

---

## 16. Object preparation

For a story-critical prop:

- Make it clearly visible
- Use a readable shape
- Avoid partial occlusion
- Keep its color distinct
- Place it near the intended interaction path
- Avoid duplicates

The prop should be large enough to remain stable across frames.

---

## 17. Camera perspective

Perspective should be internally consistent.

Review:

- Horizon
- Floor lines
- Furniture scale
- Subject scale
- Object position

Distorted or conflicting perspective may warp further during generation.

---

## 18. Source-image resolution

A source image should contain enough detail for:

- Face
- Main clothing
- Important objects
- Background structure

But excessive tiny texture may not improve video quality and can create instability.

Quality is more important than decorative complexity.

---

## 19. Source-image approval order

Review in this order:

1. Correct subject count
2. Correct anatomy
3. Correct identity
4. Correct pose
5. Correct composition
6. Movement space
7. Background geometry
8. Lighting
9. Fine detail

Do not approve an image with incorrect anatomy because its style is attractive.

---

## 20. Source-image checklist

- One coherent scene
- One clear main subject
- Correct anatomy
- Clear silhouette
- Correct aspect ratio
- Action-compatible pose
- Sufficient movement space
- Stable background
- Clear important props
- No text or interface elements
- No conflicting subjects
- Coherent lighting
- Approved identity

---

## 21. Plain-language explanation

The source image is the first animation drawing and the visual contract for the shot.

If the first drawing contains a bad hand, crowded composition, or no room for movement, the animation begins with those problems already present.

Prepare the image for motion, not only for still-image beauty.

---

## 22. Important terminology

| Term | Meaning |
|---|---|
| Silhouette | Outer readable shape of a subject |
| Movement space | Empty area available for action |
| Aspect ratio | Relationship between width and height |
| Framing | Visible area and subject scale |
| Starting pose | Body position in the opening image |
| Collage | Multiple separate images combined in one frame |
| Conflicting subject | Extra entity that may confuse generation |
| Perspective | Geometric relationship of objects in depth |
| Subject separation | Visual distinction between subject and background |
| Story-critical prop | Object required for the action or narrative |

---

## 23. Practical activity

Evaluate this proposed source image:

```text
A character stands at the far right edge, one hand hidden behind the body, feet cropped, dark hair merging into a dark wall, two background people, a small sign with text, and a red ball partly outside the frame. The requested action is walking right and picking up the ball.
```

List every issue and propose a corrected composition.

---

## 24. Expected result

Issues:

- No rightward movement space
- Feet cropped for walking
- Hidden hand for object interaction
- Hair merges with background
- Extra background subjects
- Unwanted text
- Ball partly outside frame
- Action path unclear

Corrected composition:

- Character left of center
- Full body and feet visible
- Both hands readable
- Lighter background behind hair
- No background people
- Text removed
- Ball fully visible on the right
- Clear ground plane and walking path

---

## 25. Failure analysis

### Failure 1 — Beautiful portrait used for full-body action

**Result:** Body movement is invented poorly or framing changes.

### Failure 2 — Character sheet used as source

**Result:** Multiple versions of the character may appear.

### Failure 3 — Small prop disappears

**Cause:** Prop is too small, occluded, or visually weak.

### Failure 4 — Background people become active subjects

**Cause:** The model interprets them as part of the scene.

### Failure 5 — Cropped feet create sliding motion

**Cause:** Ground contact and leg motion are not visible in the condition.

---

## 26. Short quiz

1. Why is a clear silhouette important?
2. Why should anatomy be corrected before generation?
3. What is movement space?
4. Why should aspect ratio be decided early?
5. Why are collages poor source images?
6. Why should unwanted text be removed?
7. What makes a prop easier to preserve?
8. What should be reviewed before fine style detail?

---

## 27. Quiz answers

1. It helps the model distinguish body parts and objects.
2. Source defects may be preserved or amplified.
3. Empty visual room available for the intended action.
4. Changing it later may crop or distort the planned composition.
5. They introduce multiple views, poses, or scenes that confuse conditioning.
6. It may distort, flicker, or become embedded in the video.
7. Clear shape, readable size, distinct color, and visible placement.
8. Subject count, anatomy, identity, pose, composition, and movement space.

---

## 28. Completion checklist

- [ ] I can evaluate silhouette and anatomy.
- [ ] I can plan movement space.
- [ ] I can match framing and pose to action.
- [ ] I understand why collages and text are harmful.
- [ ] I can remove conflicting subjects.
- [ ] I can prepare a readable prop and background.
- [ ] I can use a source-image approval order.
- [ ] I can redesign a still image specifically for motion.
