# Module 9

## Lesson 32 of 40 — What TI2V Means in Wan

**Study time:** approximately 20 minutes  
**Practice time:** approximately 20 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- explain the meaning of TI2V in the Wan 2.2 course;
- distinguish text-only and image-conditioned operation;
- explain why TI2V-5B is one model with two input modes;
- choose whether an image should be supplied for a shot;
- understand which creative decisions remain uncontrolled in each mode;
- design a fair comparison between TI2V text and image modes.

---

## 2. Core definition

The course defines Wan 2.2 TI2V-5B as one model that supports two modes.

```text
No image supplied:
Text → Video

Image supplied:
Image + text → Video
```

The image is therefore not a small optional decoration. Its presence changes the conditioning problem.

---

## 3. Text-only mode

In text-only mode, TI2V must create the complete visual starting state.

The text condition may describe:

- subject;
- appearance;
- environment;
- action;
- camera;
- lighting;
- visual style;
- stability constraints.

The model must decide:

- exact face or object design;
- scene composition;
- initial pose;
- background layout;
- object placement;
- movement trajectory;
- fine visual details.

This gives more creative freedom but weaker exact visual control.

---

## 4. Image-conditioned mode

When an image is supplied, the model receives a visual condition defining the initial shot.

The image strongly influences:

- subject appearance;
- composition;
- main colors;
- background;
- camera angle;
- starting pose;
- initial object positions.

The text should then focus mainly on:

- what changes;
- how quickly it changes;
- emotional development;
- camera behavior;
- invariants.

The model still generates future frames, so exact identity and trajectory are not guaranteed.

---

## 5. One model, two conditioning paths

Conceptually:

```text
                       ┌───────────────┐
Text embeddings ──────►│               │
                       │ TI2V-5B       │──► generated latent video
Optional image latent ►│               │
                       └───────────────┘
```

In text-only mode, the model must organize the initial latent state from text and learned priors.

In image-conditioned mode, encoded image information anchors the initial visual structure.

---

## 6. What does not change between modes

Both modes still require the model to solve:

- temporal consistency;
- movement generation;
- camera behavior;
- prompt interpretation;
- object permanence;
- latent sampling;
- VAE reconstruction.

Supplying an image reduces uncertainty about the starting appearance, but it does not remove the difficulty of video generation.

---

## 7. What changes between modes

| Question | Text-only mode | Image-conditioned mode |
|---|---|---|
| Who designs the first frame? | Model | Source image strongly anchors it |
| Exact character control | Lower | Higher at the start |
| Composition control | Prompt-dependent | Stronger |
| Motion control | Prompt-dependent | Prompt-dependent |
| Identity guarantee | No | Still no guarantee |
| Best use | Exploration and drafts | Controlled animation drafts |

---

## 8. Choosing text-only mode

Use text-only mode when:

- no approved image exists;
- you are exploring scene ideas;
- exact recurring identity is not important;
- you need several alternative compositions;
- the shot is environmental or establishing;
- you are testing prompt language before committing to visual design.

Example:

```text
A small sailing boat crosses a calm lake at sunrise, wide shot,
soft mist, slow movement, stable horizon.
```

The model is free to design the boat, lake, mist, and composition.

---

## 9. Choosing image-conditioned mode

Use an image when:

- a character or product design is approved;
- color palette must be preserved;
- location composition is already planned;
- the shot must begin from a specific pose;
- you need stronger continuity with another shot;
- text-only generations vary too much.

Example motion direction:

```text
The character slowly reaches toward the red book.
Her feet and torso remain still. The camera remains locked.
```

The image already communicates the character and room design.

---

## 10. Why TI2V is useful for production planning

TI2V-5B allows a team to use one model for two early-stage tasks:

1. explore new shots from text;
2. test movement on approved images.

This creates a consistent drafting environment.

A production may use TI2V to answer questions such as:

- Is the shot concept visually understandable?
- Does the action fit the duration?
- Does the source image have enough movement space?
- Does the camera direction conflict with the action?
- Which prompt wording produces the clearest motion?

The chosen setup can later be compared with a larger production model.

---

## 11. TI2V is not “text plus image must always be used”

The name can be misunderstood.

It does not mean every generation requires both a text prompt and an image in the same way.

The course definition is:

```text
Text mode:
text condition without image

Image mode:
image condition plus text direction
```

Text remains important in image mode because the image shows a state but does not explain the intended future action.

---

## 12. Prompt responsibility by mode

### Text-only prompt

Must describe both state and change:

```text
Subject + appearance + action + environment + camera + lighting + style
```

### Image-conditioned prompt

Should emphasize change:

```text
Movement + emotion + camera behavior + invariants
```

Repeating every visible detail from the image may add noise or conflicting language. The image is already the visual condition.

---

## 13. Fair comparison experiment

Create one shot concept:

```text
A girl with black hair turns toward a red ball and smiles.
```

### Run A — text-only

Describe the full character, environment, camera, and action.

### Run B — image-conditioned

Use an approved image and describe only movement, expression, camera, and invariants.

Keep as many other settings as possible unchanged.

Review:

- character identity;
- composition;
- movement clarity;
- background stability;
- prompt adherence;
- generation cost;
- usefulness as a draft.

---

## 14. Expected comparison

Text-only mode may provide:

- more varied composition;
- more varied character design;
- greater exploration;
- weaker continuity with approved assets.

Image-conditioned mode may provide:

- stronger initial identity;
- stronger composition control;
- better palette continuity;
- remaining risk of motion and identity drift.

The experiment should not ask which mode is universally better. It should ask which mode matches the shot’s constraint.

---

## 15. Failure analysis

### Text-only failure: wrong character design

The prompt describes a category, not one exact identity.

**Repair:** supply an approved image when exact identity matters.

### Text-only failure: wrong composition

The model had freedom to invent placement.

**Repair:** use clearer framing or an approved source image.

### Image-mode failure: result is nearly static

The motion direction may be too weak or constraints too restrictive.

**Repair:** request one visible action with a clear endpoint.

### Image-mode failure: face changes

The source anchors the beginning, but future views are generated.

**Repair:** reduce pose change, duration, or occlusion.

### Both modes: object disappears

Video generation still requires temporal object permanence.

**Repair:** simplify interaction and shorten the shot.

---

## 16. Plain-language explanation

TI2V is like having one animation tool that can begin in two ways.

- You can describe a scene and let it design the first picture.
- Or you can provide the first picture and ask it to animate that design.

The first approach gives freedom. The second gives stronger visual control. Both still need the model to invent movement through time.

---

## 17. Important terminology

| Term | Meaning |
|---|---|
| TI2V | Text-Image-to-Video model family in this course |
| Text-only mode | Generation without a source image |
| Image-conditioned mode | Generation guided by an image and text |
| Visual anchor | Input that stabilizes initial composition and appearance |
| Conditioning path | Route by which text or image information guides generation |
| Drafting model | Model used for experiments before final production |
| Starting state | Initial visual configuration of the shot |
| Future trajectory | Generated sequence after the starting state |

---

## 18. Short quiz

1. What determines whether TI2V behaves like T2V or I2V?
2. Does image mode remove the need for text?
3. Which mode gives more compositional freedom?
4. Which mode provides stronger initial identity control?
5. Does an image guarantee the ending pose?
6. What should an image-mode prompt emphasize?
7. Why is TI2V useful for drafting?
8. What is the correct comparison question: “Which mode is always best?” or “Which mode matches the shot constraint?”

---

## 19. Quiz answers

1. Whether an image is supplied.
2. No. Text still describes movement, acting, camera behavior, and constraints.
3. Text-only mode.
4. Image-conditioned mode.
5. No.
6. Change, motion, emotion, camera behavior, and invariants.
7. It supports both scene exploration and image-animation tests in one model.
8. Which mode matches the shot constraint.

---

## 20. Completion checklist

- [ ] I can explain both TI2V modes.
- [ ] I know what the optional image changes.
- [ ] I can choose the correct mode for a shot.
- [ ] I understand that image mode does not guarantee identity.
- [ ] I can write a mode-appropriate prompt.
- [ ] I can design a fair text-versus-image experiment.
- [ ] I can explain TI2V’s drafting role.
