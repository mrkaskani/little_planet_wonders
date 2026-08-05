# Module 7

## Lesson 27 of 40 — T2V Limitations

**Study time:** approximately 15 minutes  
**Practice time:** approximately 15 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- Explain the main limitations of T2V.
- Diagnose identity drift, prompt ambiguity, multiple-subject confusion, text-rendering problems, complex-sequence failures, and long-video drift.
- Distinguish problems that can be improved through prompting from problems requiring shot redesign.
- Decide when to replace T2V with I2V.
- Design production workarounds for difficult shots.

---

## 2. T2V freedom creates uncertainty

T2V begins without an approved source image.

The model must invent:

- Character identity
- Composition
- Environment
- Object placement
- Camera
- Motion

This high creative freedom is useful for exploration but weakens exact control.

---

## 3. Weak identity control

The prompt describes a character using words, but words do not fully define an exact face.

Across different seeds or shots, the model may change:

- Face shape
- Hair
- Age
- Clothing
- Body proportions
- Accessories

A phrase such as “young woman with black hair and a blue dress” describes a category, not one exact recurring person.

---

## 4. Character drift within one clip

Identity may change gradually during motion.

Possible symptoms:

- Hair length changes
- Face widens or narrows
- Clothing details shift
- Eye shape changes
- Body proportions change

Drift risk increases with:

- Longer duration
- Large head rotation
- Fast movement
- Complex camera motion
- Occlusion
- Multiple characters

---

## 5. Prompt ambiguity

T2V must interpret natural language.

Ambiguous prompt:

```text
A boy watches a dog beside his friend.
```

Unclear relationships can produce:

- Wrong subject performing the action
- Incorrect placement
- Extra subjects
- Missing objects

Clearer subject and action roles reduce ambiguity.

---

## 6. Multiple-subject confusion

Each additional subject adds requirements:

- Unique identity
- Correct location
- Correct action
- Correct interaction
- Stable appearance
- Correct temporal relationship

Possible failures:

- Identity swapping
- Clothing exchange
- Subject merging
- Wrong action assignment
- Character duplication
- Incorrect subject count

---

## 7. Complex object interaction

Actions involving precise contact are difficult.

Examples:

- Picking up a cup
- Passing an object between characters
- Opening a small lock
- Tying shoelaces
- Playing a musical instrument

The model must maintain:

- Hand anatomy
- Object shape
- Contact point
- Force and trajectory
- Object permanence

A simpler shot design often produces stronger results.

---

## 8. Text-rendering problems

Exact text requires precise symbol structure.

Video adds the need to preserve those symbols across frames.

Possible failures:

- Misspelled words
- Changing letters
- Distorted logos
- Unreadable signs
- Flickering labels

Critical text should usually be added during editing.

---

## 9. Complex sequence failures

A prompt may describe several sequential events:

```text
The character enters, closes the door, sits, opens a book, reads, then stands and leaves.
```

Possible results:

- Actions skipped
- Actions reordered
- Objects appear suddenly
- Character teleports
- Ending is incomplete

The prompt describes a scene sequence, but the model is generating one limited shot.

Divide long sequences into separate shots.

---

## 10. Long-video drift

As duration grows, the model must preserve more relationships across time.

Risks include:

- Identity drift
- Background changes
- Camera deviation
- Object disappearance
- Repeated motion
- Story-state loss

Shorter shots reduce the temporal consistency burden.

---

## 11. Camera-motion conflicts

T2V may add camera movement even when the action is already complex.

Potential problems:

- Subject leaves frame
- Background geometry warps
- Motion direction becomes unclear
- Character scale changes
- Identity becomes less stable

Use a fixed camera when evaluating difficult subject motion.

---

## 12. Small-detail instability

Small details are vulnerable to latent compression and temporal generation.

Examples:

- Jewelry
- Fine patterns
- Hair strands
- Fingers
- Thin objects
- Small props

Design important traits at a readable size and avoid relying on tiny detail for identity.

---

## 13. Physical plausibility limitations

The model learns common visual motion patterns but does not execute an explicit physics simulation for every shot.

Possible failures:

- Sliding feet
- Floating objects
- Incorrect weight
- Unnatural acceleration
- Impossible contact
- Changing object size

Simple, slow, familiar actions are easier.

---

## 14. When prompting may help

Prompt revision may help when:

- Subject count is unclear
- Motion direction is missing
- Camera is unspecified
- Action wording is vague
- Too many decorative details compete

Use clearer structure and one-variable experiments.

---

## 15. When a new seed may help

A new seed may help when:

- Prompt is clear
- Shot design is simple
- One candidate has an unlucky composition
- Motion path is weak in only some candidates

A seed is not a reliable solution when every candidate fails in the same way.

---

## 16. When sampling changes may help

Sampling experiments may help with:

- Incomplete detail
- Texture quality
- Motion smoothness
- Some temporal artifacts
- Prompt adherence

Sampling changes are unlikely to reliably repair:

- Fundamentally wrong subject count
- Overloaded action design
- Exact recurring identity
- Impossible source-free composition requirements

---

## 17. When to replace T2V with I2V

Use I2V when you need stronger control over:

- Character identity
- Clothing
- Color palette
- Starting pose
- Background
- Camera framing
- Object placement

T2V is strongest when invention is useful.

I2V is stronger when an approved first frame exists.

---

## 18. Shot-splitting strategy

Overloaded sequence:

```text
Character enters, crosses the room, picks up a book, sits, and speaks.
```

Split into:

```text
Shot 1: character enters the room
Shot 2: character approaches the book
Shot 3: character picks up the book
Shot 4: character sits
Shot 5: character speaks
```

Each shot has one clear production purpose.

---

## 19. Character-consistency strategy

For a recurring character:

1. Create approved reference images.
2. Use I2V for identity-sensitive shots.
3. Use T2V mainly for environments or distant views.
4. Keep wardrobe and color descriptions consistent.
5. Review face and silhouette across shots.

This hybrid strategy uses each workflow for its strength.

---

## 20. Background-consistency strategy

For a recurring location:

- Create approved location references.
- Use simple establishing shots.
- Limit complex camera motion.
- Preserve major landmarks.
- Use I2V when exact layout matters.
- Hide small differences through editing and shot variation.

---

## 21. Plain-language explanation

T2V is like asking a new film crew to recreate the same actor and set from a written description alone.

The crew may understand the idea but cast a slightly different actor, arrange the room differently, or interpret the action in another way.

Providing an approved image is like giving the crew an exact visual reference.

---

## 22. Important terminology

| Term | Meaning |
|---|---|
| Identity drift | Unwanted change in character appearance |
| Prompt ambiguity | Multiple possible interpretations of wording |
| Subject confusion | Incorrect identity, count, or action assignment |
| Object permanence | Keeping objects present and stable over time |
| Text rendering | Producing readable written symbols |
| Sequence failure | Skipped, reordered, or incomplete multi-stage actions |
| Long-video drift | Increasing inconsistency over longer duration |
| Occlusion | A subject or object becomes hidden by another element |
| Workflow replacement | Choosing I2V or another method instead of T2V |
| Shot splitting | Dividing complex action into simpler shots |

---

## 23. Practical activity

Choose the appropriate response for each case:

- Change seed
- Revise prompt
- Change sampling
- Split shot
- Replace with I2V

### Case A

One fox appears in some seeds and two in others.

### Case B

Every seed creates a different face for a recurring hero.

### Case C

Action is correct but fur remains soft.

### Case D

The character must enter, sit, open a book, and begin speaking in five seconds.

### Case E

The camera direction is unclear because the prompt says only “cinematic movement.”

---

## 24. Expected result

| Case | Best response |
|---|---|
| A | Revise prompt to state one fox, then compare seeds |
| B | Replace with I2V using approved character references |
| C | Test sampling, resolution, or model choice |
| D | Split the action into multiple shots |
| E | Revise the camera language |

---

## 25. Failure analysis

### Failure 1 — Endless seed search for exact identity

**Problem:** T2V freedom is being used for an identity-lock requirement.

**Improvement:** Move to I2V.

### Failure 2 — More steps used to fix an overloaded sequence

**Problem:** Numerical refinement cannot replace shot planning.

### Failure 3 — Critical text generated inside the video

**Problem:** Letters change across frames.

**Improvement:** Add text during editing.

### Failure 4 — Complex camera and action combined

**Problem:** Temporal workload becomes excessive.

**Improvement:** Simplify one dimension.

### Failure 5 — Long shot accepted because the first second looks good

**Problem:** Later drift is ignored.

**Improvement:** Review the entire clip and key frames.

---

## 26. Short quiz

1. Why is exact identity difficult in T2V?
2. Name three forms of character drift.
3. What problems can multiple subjects create?
4. Why is exact text difficult in video generation?
5. What is long-video drift?
6. When is a new seed appropriate?
7. When should a shot be split?
8. When should T2V be replaced with I2V?

---

## 27. Quiz answers

1. Text describes a category but does not provide an exact approved visual identity.
2. Any three of: face, hair, clothing, body proportions, accessories, age.
3. Identity swapping, merging, duplication, wrong action assignment, and count errors.
4. Precise letter shapes must be generated and preserved across frames.
5. Increasing visual or temporal inconsistency as duration grows.
6. When the prompt and shot design are clear but one random outcome is weak.
7. When one shot contains too many actions or interactions.
8. When exact character, composition, wardrobe, or location control is required.

---

## 28. Completion checklist

- [ ] I understand weak identity control in T2V.
- [ ] I can diagnose character and long-video drift.
- [ ] I can identify prompt ambiguity and subject confusion.
- [ ] I understand text-rendering and object-interaction limits.
- [ ] I know what prompting, seeds, and sampling can improve.
- [ ] I know when technical tuning is insufficient.
- [ ] I can split a complex sequence into simpler shots.
- [ ] I can decide when to replace T2V with I2V.
