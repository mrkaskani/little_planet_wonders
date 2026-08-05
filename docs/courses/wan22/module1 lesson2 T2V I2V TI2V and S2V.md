# Module 1

## Lesson 2 of 40 — T2V, I2V, TI2V, and S2V

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain T2V, I2V, TI2V, and S2V.
- Identify the inputs required by each workflow.
- Understand what each input controls.
- Choose the appropriate Wan 2.2 model for a production shot.
- Recognize the strengths and limitations of each workflow.

---

## 2. The four Wan workflows

```text
T2V:
Text → Video

I2V:
Image + text → Video

TI2V:
Text → Video
or
Image + text → Video

S2V:
Reference image + speech audio + text → Video
```

The main difference is the conditioning information supplied to the model.

| Condition | Main responsibility |
|---|---|
| Text | Subject, action, environment, camera, lighting, and style |
| Image | Initial appearance, composition, pose, colors, and background |
| Audio | Speech timing, pauses, rhythm, energy, and performance |
| Pose guidance | Broad body position and movement |

---

# 3. Text-to-Video — T2V

## Basic workflow

```text
Text description
↓
Wan T2V model
↓
Newly generated video
```

Model covered:

**Wan 2.2 T2V-A14B**

T2V begins without an approved source image. The model must invent the full scene.

### What text can control

- Subject
- Appearance
- Action
- Environment
- Camera framing
- Camera movement
- Lighting
- Visual style
- Movement speed
- Stability constraints

A useful structure is:

```text
Subject
+ appearance
+ action
+ environment
+ camera
+ lighting
+ style
+ motion constraints
```

### Strengths

- Inventing new scenes
- Establishing shots
- Visual exploration
- Situations where exact identity is not essential
- Generating multiple compositions from one concept

### Limitations

Different generations may change:

- Face
- Hair
- Clothing
- Body proportions
- Environment
- Object positions
- Camera framing

T2V is generally weak for exact recurring-character identity.

---

# 4. Image-to-Video — I2V

## Basic workflow

```text
Approved source image
+
Motion description
↓
Wan I2V model
↓
Animated video
```

Model covered:

**Wan 2.2 I2V-A14B**

### What the source image controls

- Character appearance
- Facial design
- Hair and clothing
- Starting pose
- Environment
- Object placement
- Camera framing
- Initial lighting
- Color palette

### What the motion description controls

- Character movement
- Expression
- Eye direction
- Head movement
- Hand gestures
- Object movement
- Camera behavior
- Invariants

An **invariant** is something that should remain unchanged.

Examples:

- Hair remains black.
- Clothing remains blue.
- Camera remains locked.
- Background remains stable.
- Feet remain planted.

A useful I2V structure is:

```text
Current state
+ movement
+ emotional change
+ camera behavior
+ invariants
```

### Strengths

- Approved character images
- Stronger first-frame control
- Better composition control
- More stable colors and appearance
- Specific poses and locations

### Limitations

A source image does not perfectly guarantee:

- Exact identity throughout the clip
- Exact ending pose
- Exact motion path
- Perfect facial consistency
- Perfect background stability
- Perfect object permanence

### Movement space

The source image must leave enough empty room in the intended movement direction.

---

# 5. Text-Image-to-Video — TI2V

Model covered:

**Wan 2.2 TI2V-5B**

TI2V supports two modes:

```text
Without an image:
Text → Video

With an image:
Image + text → Video
```

### Why it is useful

- Rapid experimentation
- Prompt testing
- Motion-description testing
- Comparing text-only and image-driven results
- Trying multiple seeds
- Lower-cost drafts
- Lower-resource environments

### Draft-to-production workflow

1. Create a draft with TI2V-5B.
2. Test several prompts.
3. Compare motion behavior.
4. Select the strongest setup.
5. Improve the source image if needed.
6. Generate the final shot using the appropriate A14B model.

### Limitations

Compared with A14B models, TI2V-5B may provide:

- Less fine detail
- Weaker complex motion
- More identity variation
- Lower visual richness
- Lower final production quality

Its main strengths are efficiency and flexibility.

---

# 6. Speech-to-Video — S2V

## Basic workflow

```text
Reference character image
+
Speech recording
+
Acting description
↓
Wan S2V model
↓
Speech-driven character performance
```

Model covered:

**Wan 2.2 S2V-14B**

### Responsibility of each input

#### Reference image

- Face
- Hair
- Clothing
- Body appearance
- Initial pose
- Background
- Camera framing

#### Speech audio

- Spoken timing
- Pauses
- Rhythm
- Energy
- Intonation
- Emotional emphasis
- Mouth timing
- Head and gesture rhythm

#### Acting description

- Calm or energetic delivery
- Gesture size
- Eye direction
- Facial expression
- Camera behavior
- Body stability
- Background stability

#### Optional pose guidance

- Body posture
- Hand position
- Broad physical movement

### Strengths

- Talking characters
- Lip synchronization
- Existing dialogue tracks
- Speech-driven gestures
- Emotional performance

### Limitations

Possible failures include:

- Incorrect mouth shapes
- Missed lip synchronization
- Mouth movement during silence
- Excessive gestures
- Identity drift
- Facial deformation
- Weak emotion
- Long-speech instability

---

## 7. Workflow comparison

| Workflow | Main inputs | Primary purpose | Visual control | Main motion source |
|---|---|---|---|---|
| T2V | Text | Invent a new scene | Lower | Prompt and model inference |
| I2V | Image and text | Animate an approved image | Stronger initial control | Motion description and model inference |
| TI2V | Text, optionally image | Efficient drafting | Depends on image use | Prompt and model inference |
| S2V | Image, speech, and text | Create a speaking performance | Strong initial reference | Speech, acting direction, and model inference |

---

## 8. Model-selection decision process

```text
Does the character need to speak?
├── Yes → S2V
└── No
    └── Is there an approved source image?
        ├── Yes → I2V
        └── No → T2V

Need lower-cost experimentation?
└── Consider TI2V-5B
```

---

## 9. Plain-language explanation

### T2V

“You describe the entire scene, and the model invents it.”

### I2V

“You provide the approved picture and tell the model how it should move.”

### TI2V

“One smaller model can work with text alone or with an image.”

### S2V

“You provide the character and speech, and the model creates the performance.”

---

## 10. Important terminology

| Term | Meaning |
|---|---|
| T2V | Text-to-Video |
| I2V | Image-to-Video |
| TI2V | Text-Image-to-Video |
| S2V | Speech-to-Video |
| Conditioning | Information used to guide generation |
| Source image | Image used as the visual starting state |
| Reference image | Image defining a speaking character’s appearance |
| Motion description | Text explaining movement and changes |
| Invariant | A property that should remain unchanged |
| Movement space | Empty visual room available for an action |
| Draft generation | Experimental output before final generation |
| Drift | Unwanted visual change over time |

---

## 11. Relevant generation settings

| Setting | Purpose |
|---|---|
| Workflow selection | Chooses T2V, I2V, TI2V, or S2V |
| Model checkpoint | Selects the trained model |
| Prompt | Describes content, movement, camera, and style |
| Source image | Provides the starting visual state |
| Speech audio | Provides timing and performance |
| Pose guidance | Provides optional body-motion information |
| Resolution | Controls output dimensions |
| Frame count | Controls generated duration |
| Random seed | Influences composition and motion variation |
| Sampling steps | Influences refinement and generation cost |

---

## 12. Practice activity

Choose the most appropriate workflow:

1. New aerial view of a futuristic city.
2. Animate an approved character opening a door.
3. Talking character using recorded dialogue.
4. Quickly test five forest prompts.
5. Preserve an approved character’s hair and clothing during a head turn.
6. Invent an ocean scene with a ship.
7. Lower-cost image-animation draft.
8. Teacher speaks a lesson with synchronized mouth movement.
9. Wide background shot with no identity requirement.
10. Animate a supplied product image.

---

## 13. Practice answers

| Shot | Recommended workflow |
|---|---|
| 1 | T2V |
| 2 | I2V |
| 3 | S2V |
| 4 | TI2V |
| 5 | I2V |
| 6 | T2V |
| 7 | TI2V |
| 8 | S2V |
| 9 | T2V |
| 10 | I2V |

---

## 14. Failure analysis

### Exact recurring character generated with T2V
Likely identity changes. Use approved images and I2V.

### I2V image has no movement space
Likely warping or limited action. Recompose the source image.

### TI2V draft expected to equal maximum-quality output
Use it for testing, then regenerate with the selected A14B model.

### I2V used for synchronized speech
Use S2V because speech timing is required.

### Source image assumed to guarantee perfect identity
Drift can still occur because future frames are generated.

### Too many exact characters in one T2V shot
Split into simpler shots and use approved images.

---

## 15. Short quiz

1. Which workflow begins from text only?
2. Which input defines I2V’s starting composition?
3. How does TI2V switch between text and image modes?
4. Which workflow is speech-driven?
5. What information does speech audio provide?
6. What is the strongest starting workflow for an approved character image?
7. Which model is useful for efficient experimentation?
8. Does a source image perfectly guarantee identity?

---

## 16. Quiz answers

1. T2V.
2. Source image.
3. By whether an image is supplied.
4. S2V.
5. Timing, pauses, rhythm, energy, and intonation.
6. I2V.
7. TI2V-5B.
8. No. Drift can still occur.

---

## 17. Completion checklist

- [ ] I can explain all four workflows.
- [ ] I know which inputs each workflow requires.
- [ ] I understand what text, image, and audio control.
- [ ] I can select a workflow for a production shot.
- [ ] I understand why T2V has weaker identity control.
- [ ] I understand why I2V still allows drift.
- [ ] I understand why movement space matters.
- [ ] I know when TI2V-5B is useful.
- [ ] I know when S2V should be selected.
