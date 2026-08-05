# Module 8

## Lesson 30 of 40 — Writing I2V Motion Prompts

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Write an I2V prompt that focuses on change rather than repeating the image.
- Use the structure: current state, movement, emotional change, camera behavior, and invariants.
- Specify movement direction, speed, and scope clearly.
- Balance motion with identity preservation.
- Remove conflicting or excessive constraints.
- Design controlled motion-prompt experiments.

---

## 2. Core motion-prompt structure

The course recommends:

```text
Current state
+ movement
+ emotional change
+ camera behavior
+ invariants
```

Example:

```text
The character slowly turns her head toward the red ball and smiles. Her body remains mostly still. The camera remains locked. Preserve the black hair, blue dress, garden layout, and soft morning lighting.
```

---

## 3. I2V prompt versus T2V prompt

### T2V prompt

Must describe much of the complete scene.

### I2V prompt

The source image already shows:

- Character
- Clothing
- Background
- Composition
- Starting pose

The prompt should focus primarily on what changes.

---

## 4. Current state

Briefly identify the visible starting situation when it helps clarify motion.

Examples:

- The character stands beside the table.
- The fox faces the watering can.
- The teacher is seated with both hands resting on the desk.

Do not rewrite every visual detail already obvious in the image.

---

## 5. Movement

Movement should specify:

- Body part or object
- Direction
- Speed
- Range
- Number of repetitions
- End state when important

Weak:

```text
She moves naturally.
```

Stronger:

```text
She slowly raises her right hand to shoulder height and waves once.
```

---

## 6. Movement direction

Use explicit direction when relevant:

- Turns to the left
- Walks from left to right
- Looks upward
- Reaches toward the cup
- Steps backward once
- Moves closer to the camera

Direction reduces ambiguous trajectories.

---

## 7. Movement speed

Speed language affects temporal planning.

Examples:

- Slowly
- Gently
- Gradually
- At a natural walking pace
- Quickly
- Sudden

Slow, controlled movement is generally easier for identity preservation than rapid complex action.

---

## 8. Movement scope

Limit which parts of the scene should move.

Example:

```text
Only the head and eyes move. The shoulders and body remain still.
```

Example:

```text
The right arm moves while the feet remain planted.
```

This reduces unintended full-body or camera movement.

---

## 9. Emotional change

Describe one visible emotional transition.

Examples:

- Neutral expression becomes a gentle smile
- Concerned expression becomes relaxed
- Eyes widen slightly with curiosity
- Character smiles warmly while speaking

Avoid asking for several rapid emotional states in one short shot.

---

## 10. Camera behavior

Specify one camera behavior:

- Camera remains locked
- Gentle slow push-in
- Small pan to the right
- Camera tracks the character smoothly

A fixed camera is useful when testing character motion.

Large camera motion can reveal unconditioned background regions and increase drift.

---

## 11. Invariants

An invariant is a property intended to remain unchanged.

Useful invariants:

- Preserve black hair
- Preserve blue dress
- Preserve facial identity
- Preserve garden layout
- Preserve lighting
- Keep the camera fixed
- Keep the background stable

Use only important invariants.

---

## 12. Too many invariants

Overconstrained prompt:

```text
Preserve every pixel, keep all body parts completely still, maintain exact pose, do not change anything, but make the character walk across the room.
```

The motion and invariants conflict.

An invariant should protect non-moving features without blocking the requested action.

---

## 13. Positive instructions versus negative instructions

Positive instruction:

```text
The camera remains locked and the background stays stable.
```

Negative-heavy instruction:

```text
Do not move the camera, do not change the background, do not distort anything, do not add objects.
```

Clear positive descriptions are often easier to organize.

Use negative constraints only for important recurring failures.

---

## 14. One observable action

A strong I2V prompt usually begins with one main action.

Examples:

- Turn head
- Raise hand
- Pick up cup
- Take one step
- Smile
- Open door

Multiple actions may require a longer duration or separate shots.

---

## 15. Action stages

For a pickup action:

```text
hand moves toward cup
→ fingers contact cup
→ cup lifts from table
→ hand stops
```

The prompt does not need to narrate every frame, but it should identify a plausible action endpoint.

Example:

```text
She slowly reaches with her right hand, grips the red cup, and lifts it slightly from the table.
```

---

## 16. Prompt and source-pose agreement

If the source image shows the right hand hidden, requesting a precise right-hand gesture is risky.

If the character is cropped at the waist, requesting walking is risky.

The motion prompt cannot fully compensate for missing visual information.

---

## 17. Example — Head turn

```text
The character slowly turns her head to the right and looks at the red ball. Her expression changes from neutral to a gentle smile. Her shoulders and body remain still. The camera remains locked. Preserve her face, black hair, blue dress, garden layout, and soft morning light.
```

Why it is strong:

- Clear body part
- Clear direction
- Clear speed
- One emotional change
- Controlled body scope
- Fixed camera
- Relevant invariants

---

## 18. Example — Hand wave

```text
The character slowly raises her right hand to shoulder height and waves once with a small natural movement. Her feet and torso remain still. The camera remains fixed. Preserve her facial identity, clothing, and background.
```

The prompt avoids:

- Repeated waving
- Large body movement
- Unspecified hand
- Camera ambiguity

---

## 19. Example — Walking

```text
The character walks slowly from left to right along the visible path and stops beside the blue chair. Use a natural pace with clear foot contact. The camera remains fixed. Preserve the clothing, hair, path layout, and lighting.
```

This requires a full-body source image and sufficient movement space.

---

## 20. Example — Gentle camera movement

```text
The character remains seated and looks toward the window while the camera performs a gentle slow push-in. Her pose remains stable. Preserve her face, clothing, room geometry, and lighting.
```

Only one major temporal element—the camera push—is emphasized.

---

## 21. Weak prompt examples

### Too vague

```text
Make it move beautifully.
```

### Too complex

```text
She stands, runs, jumps, turns, changes expression, picks up three objects, and the camera circles rapidly.
```

### Conflicting

```text
The camera remains locked while rotating around the subject.
```

### Redundant

A long description repeats every visible color and object but does not explain motion.

---

## 22. Motion prompt review order

1. Is the action visible in the source image?
2. Is the moving body part specified?
3. Is direction clear?
4. Is speed clear?
5. Is the action scope limited?
6. Is the emotional change simple?
7. Is camera behavior singular?
8. Are invariants relevant?
9. Do any instructions conflict?
10. Does the duration support the action?

---

## 23. Controlled prompt experiment

Keep fixed:

- Source image
- Model
- Seed
- Resolution
- Frame count
- Sampling settings

Change only one motion phrase.

Example:

```text
Run A: turns toward the ball
Run B: slowly turns her head toward the ball while her body remains still
```

Compare:

- Motion scope
- Identity
- Body stability
- Camera stability

---

## 24. Motion-strength experiment

Create three prompt versions:

### Low motion

```text
She makes a small head turn toward the ball.
```

### Medium motion

```text
She slowly turns her head and shoulders toward the ball.
```

### High motion

```text
She quickly turns her whole body and steps toward the ball.
```

Observe how motion complexity affects consistency.

---

## 25. Plain-language explanation

The source image tells the animator what the scene looks like now.

The motion prompt should answer:

- What changes next?
- How fast?
- Which parts move?
- What feeling changes?
- Does the camera move?
- What must remain the same?

---

## 26. Important terminology

| Term | Meaning |
|---|---|
| Current state | Visible starting situation |
| Motion prompt | Text directing change from the source image |
| Movement direction | Spatial path of the action |
| Movement speed | Rate at which action occurs |
| Movement scope | Parts of the subject or scene allowed to move |
| Emotional change | Visible transition in expression or feeling |
| Camera behavior | Fixed or moving viewpoint instruction |
| Invariant | Property intended to remain unchanged |
| Positive instruction | Description of the desired result |
| Overconstraint | Too many restrictions that conflict with motion |

---

## 27. Practical activity

Improve this prompt:

```text
Make the girl move and smile. Do not change anything. Make the camera cinematic.
```

The source image shows a seated girl with black hair and a blue dress beside a red book.

Create:

1. A fixed-camera expression prompt
2. A hand-and-book interaction prompt
3. A gentle-camera prompt

---

## 28. Expected result

### Fixed-camera expression

```text
The girl slowly turns her head toward the red book and smiles gently. Her body remains seated and still. The camera remains locked. Preserve her face, black hair, blue dress, room layout, and lighting.
```

### Hand-and-book interaction

```text
The girl slowly reaches with her right hand toward the red book and rests her hand on its cover. Her torso and feet remain still. The camera remains fixed. Preserve her facial identity, clothing, table, and background.
```

### Gentle-camera version

```text
The girl remains seated and looks at the red book while the camera performs a gentle slow push-in. Her pose stays stable. Preserve her face, black hair, blue dress, room geometry, and soft lighting.
```

---

## 29. Failure analysis

### Failure 1 — Video remains static

**Possible causes:** Motion wording is too weak, source pose discourages motion, or invariants block action.

### Failure 2 — Entire body moves during a head turn

**Improvement:** Limit movement scope explicitly.

### Failure 3 — Wrong hand moves

**Improvement:** Name the hand and ensure it is visible in the source image.

### Failure 4 — Identity changes during rapid motion

**Improvement:** Slow or reduce the action and shorten the shot.

### Failure 5 — Camera moves despite a character-motion test

**Improvement:** State that the camera remains locked and remove cinematic camera language.

### Failure 6 — Background warps during push-in

**Improvement:** Reduce the camera movement or simplify background geometry.

---

## 30. Short quiz

1. What are the five parts of the I2V prompt structure?
2. Why should I2V prompts focus on change?
3. What information should movement specify?
4. What is movement scope?
5. What is an invariant?
6. Why can too many invariants be harmful?
7. Why should the prompt agree with the source pose?
8. What should remain fixed during a motion-wording experiment?

---

## 31. Quiz answers

1. Current state, movement, emotional change, camera behavior, and invariants.
2. The image already defines the initial visual scene.
3. Body part or object, direction, speed, range, repetition, and endpoint where relevant.
4. Which parts of the subject or scene are allowed to move.
5. A property intended to remain unchanged.
6. They may conflict with the requested movement and produce static or unstable output.
7. The model cannot reliably animate hidden or incompatible body information.
8. Source image, model, seed, resolution, frame count, and sampling settings.

---

## 32. Completion checklist

- [ ] I can use the five-part I2V motion-prompt structure.
- [ ] I can focus on changes instead of redescribing the image.
- [ ] I can specify direction, speed, scope, and endpoint.
- [ ] I can direct one emotional change.
- [ ] I can define one camera behavior.
- [ ] I can choose relevant invariants.
- [ ] I can remove conflicts and overconstraints.
- [ ] I can design controlled motion-prompt experiments.
