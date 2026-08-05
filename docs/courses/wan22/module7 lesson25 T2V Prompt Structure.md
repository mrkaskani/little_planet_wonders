# Module 7

## Lesson 25 of 40 — T2V Prompt Structure

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Build a structured T2V prompt.
- Separate subject, appearance, action, environment, camera, lighting, style, and constraints.
- Prioritize structural instructions over decorative detail.
- Reduce ambiguity and conflicting directions.
- Design prompts suitable for controlled experiments.
- Review a prompt before generation.

---

## 2. Core prompt structure

The course recommends:

```text
Subject
+ appearance
+ action
+ environment
+ camera
+ lighting
+ visual style
+ motion constraints
```

This is a planning framework, not a requirement to make every prompt long.

Use only categories that contribute to the shot.

---

## 3. Subject

The subject identifies the main entity.

Examples:

- One small fox
- A wooden sailing boat
- One young woman
- A yellow bird
- A red delivery vehicle

When count matters, state it explicitly.

```text
One fox
```

is clearer than:

```text
Foxes in a garden
```

---

## 4. Appearance

Appearance describes stable visible traits.

Examples:

- Small red fox with a white chest
- Young woman with long black hair and a blue dress
- Old wooden boat with a white sail

Avoid overloading appearance with many tiny details that are difficult to preserve.

Prioritize:

- Silhouette
- Main colors
- Clothing
- Distinctive medium-sized features

---

## 5. Action

The action explains what changes over time.

A strong action is:

- Observable
- Simple
- Directional
- Appropriate for the duration

Examples:

- Walks slowly from left to right
- Turns toward the red ball
- Opens the wooden door
- Sits on the chair

Avoid asking for many sequential actions in one short shot.

---

## 6. Environment

The environment establishes the scene.

Examples:

- Bright flower garden
- Quiet wooden classroom
- Calm lake at sunrise
- Narrow city street after rain

The environment should support rather than compete with the subject.

Very complex backgrounds create more opportunities for temporal instability.

---

## 7. Camera framing

Framing defines how much of the subject and environment are visible.

Common choices:

- Wide shot
- Medium-wide shot
- Medium shot
- Close-up
- Eye-level
- Low-angle
- High-angle

Framing should match the action.

A full-body action requires enough visible space.

A facial reaction may benefit from a closer shot.

---

## 8. Camera movement

Camera movement can include:

- Fixed camera
- Slow push-in
- Slow pull-back
- Gentle pan
- Tracking movement

Use one clear camera behavior.

A complex subject action plus complex camera movement creates competing temporal demands.

For early experiments, a fixed camera provides a cleaner motion test.

---

## 9. Lighting

Lighting language may describe:

- Time of day
- Direction
- Softness
- Color temperature
- Contrast

Examples:

- Soft morning light
- Warm sunset light
- Diffused indoor light
- Cool moonlight

Avoid incompatible lighting instructions such as soft overcast light and dramatic hard shadows unless the combination is intentional.

---

## 10. Visual style

Style describes the intended visual treatment.

Examples:

- Realistic cinematic
- Calm child-friendly animation
- Soft illustrated look
- Natural documentary style
- Stylized miniature world

Style should remain compatible with the subject, lighting, and action.

---

## 11. Motion constraints

Motion constraints describe what should remain controlled.

Examples:

- Stable background
- Character remains the only subject
- Camera remains fixed
- Slow natural movement
- No sudden motion
- Body proportions remain stable

Constraints should be short and relevant.

Too many negative instructions can make a prompt difficult to follow.

---

## 12. Example structured prompt

```text
One small red fox with a white chest walks slowly from left to right along a stone path in a bright flower garden. Medium-wide eye-level shot, fixed camera, soft morning light, calm child-friendly animation, natural walking motion, stable background.
```

Prompt map:

| Category | Text |
|---|---|
| Subject | One small fox |
| Appearance | Red with a white chest |
| Action | Walks slowly left to right |
| Environment | Bright flower garden with a stone path |
| Camera | Medium-wide, eye-level, fixed |
| Lighting | Soft morning light |
| Style | Calm child-friendly animation |
| Constraints | Natural motion, stable background |

---

## 13. Order of importance

When a prompt becomes long, place the most important requirements early and clearly.

Recommended priority:

1. Subject and count
2. Main action
3. Critical object relationship
4. Camera framing
5. Environment
6. Lighting
7. Style
8. Secondary details

The exact order is flexible, but structural requirements should not be buried.

---

## 14. One subject, one action, one camera rule

A reliable starting pattern is:

```text
One main subject
+
one main action
+
one camera behavior
```

Example:

```text
One girl turns toward a red ball while the camera remains fixed.
```

This reduces:

- Subject confusion
- Action skipping
- Camera conflict
- Identity mixing

---

## 15. Prompt ambiguity

Ambiguous prompt:

```text
A girl watches a dog running beside her friend.
```

Questions:

- Whose friend?
- Who is running?
- Is the dog beside the girl or the friend?
- Which subject should the camera follow?

Clearer version:

```text
One girl stands still on the left while one brown dog runs past her from right to left. Medium-wide fixed shot.
```

---

## 16. Conflicting instructions

Conflict example:

```text
Fixed camera with a rapid circular tracking movement.
```

Conflict example:

```text
The character remains completely still while walking forward.
```

Conflict example:

```text
Soft flat lighting with sharp dramatic shadows from every direction.
```

Remove contradictions before testing the model.

---

## 17. Overloaded prompt

```text
Four characters run, dance, exchange objects, change clothes, enter a car, drive away, while the camera circles and zooms through a crowded market.
```

This requires many difficult decisions:

- Four identities
- Multiple actions
- Object permanence
- Costume changes
- Vehicle interaction
- Complex camera
- Crowded background

Split it into separate shots.

---

## 18. Prompt detail budget

Every detail creates another requirement the model may need to satisfy.

Use detail for:

- Story-critical identity
- Story-critical object
- Action clarity
- Camera clarity
- Visual continuity

Avoid adding decorative requirements that do not affect the shot’s purpose.

---

## 19. Prompt extension review

When using prompt extension, compare the expanded prompt with the original intent.

Check for:

- Extra characters
- Extra objects
- New actions
- Changed camera
- Changed lighting
- Changed style
- Increased background complexity

Remove additions that create unnecessary difficulty.

---

## 20. Controlled prompt experiment

To test prompt wording:

Keep fixed:

- Model
- Seed
- Resolution
- Frame count
- Sampling settings

Change only one wording category.

Example:

```text
Run A: walks through the garden
Run B: walks slowly from left to right through the garden
```

This tests action specificity.

---

## 21. Prompt review checklist

Before generation, ask:

- Is the subject count explicit?
- Is there one main action?
- Is movement direction clear?
- Is the environment necessary and readable?
- Does the framing show the action?
- Is camera behavior singular and clear?
- Are lighting and style compatible?
- Are the constraints relevant?
- Are there any contradictions?
- Should the shot be divided?

---

## 22. Plain-language explanation

A prompt is like a concise direction given to a film crew.

A weak direction says:

```text
Make something beautiful with a fox.
```

A strong direction says:

```text
One red fox walks slowly left to right through a bright garden. Use a medium-wide fixed shot in soft morning light.
```

The second direction leaves less structural ambiguity.

---

## 23. Important terminology

| Term | Meaning |
|---|---|
| Subject | Main entity in the shot |
| Appearance | Stable visible traits |
| Action | Change occurring over time |
| Environment | Location and surrounding scene |
| Framing | How much of the scene is visible |
| Camera movement | Motion of the viewpoint |
| Lighting | Direction and quality of illumination |
| Visual style | Overall aesthetic treatment |
| Constraint | Requirement limiting unwanted change |
| Ambiguity | Wording with multiple possible interpretations |
| Conflict | Instructions that cannot all be satisfied consistently |
| Prompt extension | Expansion of a short prompt into more detail |

---

## 24. Practical activity

Rewrite this weak prompt:

```text
A woman gets a book in a room and looks happy while the camera does something cinematic.
```

Create three versions:

1. Simple fixed-camera version
2. Version with one controlled camera movement
3. Version split into two shots

---

## 25. Expected result

### Simple version

```text
One young woman with black hair walks to a wooden table and picks up one red book. Medium-wide eye-level shot, fixed camera, soft indoor light, slow natural movement, stable room.
```

### Controlled-camera version

```text
One young woman with black hair picks up one red book from a wooden table and smiles. Medium shot with a gentle slow push-in, soft indoor light, stable background.
```

### Two-shot version

```text
Shot 1: One young woman walks toward a wooden table holding one red book. Medium-wide fixed shot.

Shot 2: The woman picks up the red book and smiles. Medium close-up with a gentle push-in.
```

---

## 26. Failure analysis

### Failure 1 — Wrong number of characters

**Improvement:** State the count explicitly and remove unnecessary background people.

### Failure 2 — Action occurs in wrong direction

**Improvement:** Add clear left-to-right or toward-camera language.

### Failure 3 — Camera moves unexpectedly

**Improvement:** State fixed camera or one specific movement.

### Failure 4 — Prompt is ignored despite being long

**Cause:** Important instructions may be buried among decorative details.

### Failure 5 — Character performs only part of the action

**Cause:** Too many sequential actions for one shot.

**Improvement:** Split the sequence.

---

## 27. Short quiz

1. What are the eight prompt categories in the course structure?
2. Why should subject count be explicit?
3. Why is one main action easier than several sequential actions?
4. What is a motion constraint?
5. Give one example of conflicting camera language.
6. What should remain fixed during a prompt wording experiment?
7. Why can a longer prompt perform worse?
8. When should a shot be divided?

---

## 28. Quiz answers

1. Subject, appearance, action, environment, camera, lighting, style, and motion constraints.
2. To reduce uncertainty about how many subjects should appear.
3. It requires fewer temporal decisions and reduces action skipping.
4. A requirement limiting unwanted change, such as fixed camera or stable background.
5. “Fixed camera with a rapid circular tracking move.”
6. Model, seed, resolution, frame count, and sampling settings.
7. It may contain conflicts, buried priorities, or too many requirements.
8. When the action contains too many stages or competing camera and subject demands.

---

## 29. Completion checklist

- [ ] I can build a structured T2V prompt.
- [ ] I can identify every prompt category.
- [ ] I can prioritize structural requirements.
- [ ] I can remove ambiguity and conflicts.
- [ ] I understand the one-subject, one-action, one-camera rule.
- [ ] I can review an expanded prompt.
- [ ] I can design a controlled wording experiment.
- [ ] I know when to split a complex prompt into multiple shots.
