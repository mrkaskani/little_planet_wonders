# Module 8

## Lesson 31 of 40 — I2V Identity and Motion Failures

**Study time:** approximately 20 minutes  
**Practice time:** approximately 20 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- distinguish identity drift from motion failure;
- diagnose face, hair, clothing, background, and camera instability;
- explain why a strong first frame does not guarantee a stable final frame;
- identify when a prompt is too restrictive or too permissive;
- regenerate a failed shot by changing only one variable at a time;
- decide whether to repair the prompt, source image, shot duration, camera plan, or workflow;
- create a repeatable I2V review report.

---

## 2. Core principle

Image-to-Video begins with more visual control than Text-to-Video because the source image already defines the first visible state. It establishes the initial character, environment, color palette, pose, framing, and object placement.

However, the source image controls the **starting condition**, not every future frame.

```text
Approved source image
+ motion description
+ random latent future
→ generated temporal trajectory
→ visible video
```

The model must invent all intermediate states after the first frame. Every invented state creates an opportunity for drift, deformation, unwanted motion, or camera conflict.

---

## 3. Identity consistency versus motion consistency

These are related but different review categories.

### Identity consistency

Identity consistency asks whether the subject remains recognizably the same.

Review:

- face shape;
- eye shape and spacing;
- nose and mouth structure;
- hair color, length, and style;
- clothing colors and major design features;
- body proportions;
- accessories;
- age and visual style.

### Motion consistency

Motion consistency asks whether movement develops naturally and logically.

Review:

- correct movement direction;
- believable intermediate poses;
- stable limb length;
- continuous object trajectories;
- contact between hand and object;
- movement speed;
- acceleration and stopping;
- camera behavior;
- absence of teleportation or sliding.

A video can preserve identity while producing poor movement. It can also produce smooth movement while gradually changing the character.

---

## 4. Why identity drift happens

Identity drift is an unwanted change in the subject across generated frames.

The risk increases when the model must infer visual information that is not clearly visible in the source image.

Examples:

- a front-facing source image must rotate into a side view;
- one side of the face is hidden;
- hands are outside the frame and later become visible;
- hair moves away from the face and exposes unseen areas;
- the character turns around and reveals the back of the clothing;
- an object passes in front of the face;
- the camera moves into a different angle.

The model must construct these unseen regions from learned patterns. The result may remain plausible but stop matching the approved identity.

---

## 5. Common identity failures

### 5.1 Face changes

Symptoms:

- face becomes wider or narrower;
- eyes change size;
- nose changes shape;
- age appears to change;
- smile produces a different person;
- profile view does not match the front view.

Likely pressure points:

- large head turn;
- extreme expression;
- source image lacks facial detail;
- face occupies too few pixels;
- long shot duration;
- fast camera movement;
- partial occlusion.

### 5.2 Hair changes

Symptoms:

- black hair becomes brown;
- long hair becomes short;
- hairstyle changes during motion;
- hair merges with the background;
- loose strands appear and disappear.

Hair is difficult because it combines identity, fine texture, deformable motion, and changing silhouettes.

### 5.3 Clothing changes

Symptoms:

- dress color shifts;
- sleeve length changes;
- patterns flicker;
- buttons or pockets appear and disappear;
- clothing shape changes during body movement.

Fine clothing patterns are less stable than broad color blocks and simple silhouettes.

---

## 6. Image drift

**Image drift** is broader than identity drift. It means the generated shot gradually moves away from the visual rules established by the source image.

Possible drift includes:

- altered character appearance;
- changing lighting;
- redesigned background;
- moving furniture;
- altered color palette;
- changed camera position;
- object duplication;
- scene geometry changes.

A useful review question is:

> If I compare the final frame with the source image, does it still look like the same production design and location?

---

## 7. Background warping

Background warping occurs when environmental geometry bends, stretches, slides, or changes during motion.

Typical causes include:

- complex repeated textures;
- fast camera movement;
- subject movement covering and revealing large areas;
- source image with inconsistent perspective;
- insufficient separation between subject and background;
- asking the model to keep the background fixed while also requesting a moving camera.

Examples:

- window frames bend;
- floor lines curve;
- trees shift position;
- table edges grow or shrink;
- doors change width;
- the horizon moves unexpectedly.

A fixed camera and simpler background provide a cleaner test of character motion.

---

## 8. Excessive movement

An I2V prompt may create more movement than requested.

Symptoms:

- full body moves when only the head should move;
- camera pushes in without permission;
- background elements animate;
- clothing flutters strongly in a calm room;
- the character makes large gestures during quiet speech;
- facial expression becomes exaggerated.

This often happens when the prompt includes energetic language or when movement constraints are vague.

Better direction:

```text
The character slowly turns her head toward the ball.
Her shoulders, torso, and feet remain still.
The camera remains locked.
```

The important improvement is not merely saying “less movement.” It is specifying which parts may move and which parts must remain stable.

---

## 9. Static-video failure

The opposite problem is a nearly static result.

Symptoms:

- the image only breathes or flickers;
- requested hand movement never occurs;
- head movement is too small to read;
- only the camera moves;
- facial expression does not change.

Possible reasons:

- motion request is too weak or abstract;
- prompt contains too many preservation constraints;
- source pose does not support the action;
- movement space is insufficient;
- action is difficult or ambiguous;
- the model selects a low-motion interpretation to protect identity.

A useful repair is to request one clear, observable movement with direction and endpoint.

---

## 10. Camera-motion conflicts

Camera instructions and subject instructions may compete.

Example conflict:

```text
The character walks toward the right.
The camera tracks left.
Preserve the exact background composition.
```

These requirements cannot all remain visually identical. Tracking changes the visible background and relative subject position.

Choose one primary motion system for early tests:

- fixed camera with subject movement; or
- mostly still subject with controlled camera movement.

Combining complex camera motion with complex body movement raises temporal difficulty and makes failure attribution harder.

---

## 11. Diagnostic architecture map

```text
Source image quality
        │
        ▼
Initial latent condition
        │
        ▼
Motion interpretation
        │
        ▼
Temporal generation
        │
        ▼
VAE reconstruction
        │
        ▼
Visible result
```

Use this map to ask where the failure probably began.

- Defect already visible in source → repair source image.
- Wrong action direction → prompt or motion interpretation.
- Identity changes during rotation → temporal generation and unseen-view inference.
- Fine texture flickers but structure is stable → temporal detail or decoding.
- Camera moves unexpectedly → prompt conflict or generative interpretation.

---

## 12. One-variable-at-a-time regeneration

Do not change five things after one failed result.

Weak experiment:

- new source image;
- new prompt;
- new seed;
- longer duration;
- different resolution.

You will not know which change helped.

Controlled experiment:

| Run | Source image | Prompt | Seed | Duration | Changed variable |
|---|---|---|---|---|---|
| 1 | A | P1 | 100 | Short | Baseline |
| 2 | A | P2 | 100 | Short | Prompt only |
| 3 | A | P1 | 200 | Short | Seed only |
| 4 | A | P1 | 100 | Shorter | Duration only |

This produces diagnostic knowledge instead of random trial and error.

---

## 13. Practical experiment

Use a source image showing one character in a medium shot.

Target action:

```text
The character slowly turns her head toward a red ball and smiles.
Her torso remains still. The camera remains locked.
```

Create four planned tests:

1. Baseline.
2. Same setup with a simpler smile.
3. Same setup with a smaller head turn.
4. Same setup with a shorter duration.

Review:

- face identity;
- hair shape;
- eye direction;
- smile naturalness;
- torso stability;
- background geometry;
- camera stability.

---

## 14. Expected result

A strong result should change only:

- head angle;
- eye direction;
- facial expression.

It should preserve:

- face identity;
- hair color and general hairstyle;
- clothing;
- torso position;
- background;
- lighting;
- camera framing.

A smaller head turn may preserve identity better than a large profile rotation. A shorter shot may reduce accumulated drift. A simpler smile may reduce facial redesign.

---

## 15. Failure analysis table

| Symptom | Likely category | First repair to test |
|---|---|---|
| Face changes during turn | Identity drift | Reduce head rotation |
| Hair color shifts | Appearance drift | Strengthen broad invariant and simplify lighting |
| Dress pattern flickers | Fine-detail instability | Simplify pattern or shorten shot |
| Background bends | Geometry instability | Lock camera and simplify background |
| Character barely moves | Static-video failure | Make one movement explicit and observable |
| Whole body moves | Excessive motion | State permitted and forbidden body movement |
| Camera pans unexpectedly | Camera conflict | Explicit fixed-camera instruction |
| Hand duplicates | Motion/anatomy failure | Slow and simplify gesture |
| Object disappears | Object-permanence failure | Simplify interaction and shorten clip |

---

## 16. Plain-language explanation

The source image is like the first drawing in an animation sequence. It gives the model a strong starting picture, but the model must draw all later pictures itself.

If the character turns, smiles, or moves behind an object, the model must invent views that were not visible in the first drawing. The farther the action travels from the source pose, the more opportunity there is for the design to change.

---

## 17. Important terminology

| Term | Meaning |
|---|---|
| Identity drift | Unwanted change in the character’s defining appearance |
| Image drift | Broader movement away from source-image design |
| Background warping | Unwanted deformation of environmental geometry |
| Static-video failure | Requested movement is absent or too weak |
| Excessive movement | More movement occurs than requested |
| Motion conflict | Two movement instructions compete |
| Invariant | Property intended to remain unchanged |
| Object permanence | Object remains present and coherent over time |
| Failure attribution | Estimating which production stage caused a problem |
| Controlled experiment | Test that changes only one variable |

---

## 18. Short quiz

1. Does the source image guarantee the final frame?
2. What is the difference between identity drift and image drift?
3. Why can a large head turn change the face?
4. What is static-video failure?
5. Why is a fixed camera useful during motion testing?
6. What should be changed in a controlled experiment?
7. Why are fine clothing patterns unstable?
8. What is the first action when a defect already exists in the source image?

---

## 19. Quiz answers

1. No. It strongly controls the starting condition, but future frames are generated.
2. Identity drift changes the subject; image drift can also change background, lighting, camera, or objects.
3. The model must invent facial regions and geometry not visible in the source.
4. The generated result contains little or none of the requested action.
5. It removes one major source of temporal change and makes diagnosis easier.
6. One variable only.
7. They require precise high-frequency detail to remain stable across frames.
8. Repair the source image before generation.

---

## 20. Completion checklist

- [ ] I can separate identity failures from motion failures.
- [ ] I can identify face, hair, clothing, and background drift.
- [ ] I understand why unseen views increase risk.
- [ ] I can diagnose static and excessive movement.
- [ ] I can identify camera-motion conflicts.
- [ ] I can design a one-variable experiment.
- [ ] I can write a structured failure report.
- [ ] I know when to repair the source image instead of the prompt.
