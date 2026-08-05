# Module 25

## Lesson 52 of 72 — Multi-Action Shots and Segment Chains

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Identify when a planned shot contains too many actions for one generation unit.
- Break complex motion into A→B, B→C, and C→D segments.
- Use shared boundary frames to preserve continuity.
- Track body, props, camera, emotion, and screen direction across the chain.
- Create a Multi-Action Segment Chain.

---

# 2. Why it matters for children under five

A shot may be conceptually continuous while still containing several important actions. For example, Lumi notices the ball, walks toward it, picks it up, and shows it. Asking one generation to perform all four actions often produces skipped movement, identity drift, strange hands, camera changes, or incorrect prop state.

The better workflow keeps the shot’s camera and story purpose but divides the motion into smaller controlled segments. The ending frame of one segment becomes the starting frame of the next.

This structure improves review and local repair. If the pickup fails, the production can regenerate only B→C rather than recreating the entire shot.


## Recurring example series

All examples continue the same evolving preschool series:

# Lumi and Pip’s Little Garden

- **Lumi:** a curious four-year-old child with warm brown skin, a dark curly bob, coral overalls, a cream shirt, yellow boots, and a leaf-shaped hair clip.
- **Pip:** a small rounded teal-blue bird with a cream belly, orange beak, sky-blue scarf, large expressive eyes, gentle hops, and short calm flights.
- **Auntie Noura:** a patient adult guide with warm medium-brown skin, dark hair in a low bun, a sage-green gardening apron, a plum shirt, and calm reassuring movement.
- **World:** Sunseed Garden, including the Rainbow Garden, Cozy Workshop, and Little Pond Path.
- **Visual identity:** rounded 2D cut-paper design, soft texture, simple facial features, clear silhouettes, stable eye-level camera, warm light, and uncluttered backgrounds.
- **Audio identity:** warm voices, short sentences, restrained music, clear ambience, gentle Foley, and protected quiet space.


---

# 3. Core concepts

## 1. Shot versus segment

One shot is one continuous camera view. One shot may contain several generated segments when the action is complex.

## 2. Action inventory

List every meaningful verb in the shot. Each verb may require its own segment.

## 3. Boundary state

A boundary is a stable pose and state between actions. It should look complete enough to hold and continue.

## 4. A→B structure

Segment A→B starts at state A and ends at state B. State B becomes the exact source for the next segment.

## 5. Shared boundary image

Reusing the same approved boundary frame reduces visual discontinuity and prop drift.

## 6. Camera continuity

Camera height, framing, perspective, and screen direction remain fixed when the shot is meant to feel continuous.

## 7. Body continuity

Track feet, torso, hands, head, gaze, and balance at each boundary.

## 8. Prop continuity

Track holder, hand, location, orientation, and state at every segment.

## 9. Emotional continuity

Emotion should progress gradually. Curiosity may become satisfaction, but not jump to fear or celebration without a story reason.

## 10. Segment duration intention

Give each action enough time to read. Walking may need longer than a small head turn.

## 11. Boundary review

The editor should compare the final usable frame of one segment with the first frame of the next.

## 12. Local regeneration

Only the failed segment and its affected boundary need revision when the rest passes.


---

# 4. Practical example from the ongoing series

## Planned shot

Lumi notices the red ball, approaches it, picks it up, and shows it.

## Segment A→B — Notice

**A:** Lumi faces forward, hands empty.  
**B:** Lumi’s head and eyes turn toward the ball.

## Segment B→C — Approach

**B:** Lumi looks at the ball.  
**C:** Lumi stands beside the ball, feet stable.

## Segment C→D — Pickup

**C:** Lumi stands beside the ball, hands empty.  
**D:** Lumi holds the ball at waist height.

## Segment D→E — Show

**D:** Ball at waist height.  
**E:** Ball held at chest height toward the audience.

The camera remains locked throughout. Every segment contains one action, and every boundary preserves prop and body state.

---

# 5. Reusable context template

# Multi-Action Segment Chain

**Episode, scene, shot:**  
[IDs]

**Shot purpose:**  
[What the continuous shot communicates]

**Camera:**  
[Locked or one continuous behavior]

**Action inventory:**  
1. [Verb]
2. [Verb]
3. [Verb]

## State A

- Character:
- Pose:
- Prop:
- Emotion:
- Camera:
- Background:

## Segment A→B

**Action:**  
[One]

**Allowed changes:**  
[List]

**Unchanged:**  
[List]

**Duration intention:**  
[Description]

**Approval criteria:**  
[List]

## State B

[Complete boundary state]

## Segment B→C

[Repeat]

## State C

[Complete boundary state]

## Segment C→D

[Repeat]

## State D

[Complete boundary state]

## Chain continuity

- Camera match:
- Screen direction:
- Character scale:
- Lighting:
- Background:
- Wardrobe:
- Prop holder:
- Hand occupancy:
- Emotion:
- Audio continuity:

## Regeneration rule

[Which unit is regenerated when a failure occurs]

---

# 6. Reusable prompt template

Break the following planned shot into a controlled segment chain.

**Planned shot action**  
[Describe all intended actions]

1. List every meaningful action verb.
2. Create stable states A, B, C, D, and additional states if required.
3. Create one segment per primary action.
4. Use each ending state as the next starting state.
5. Preserve camera, screen direction, identity, lighting, location, and approved prop design.
6. Track feet, hands, gaze, expression, prop holder, and orientation at each boundary.
7. Define duration intention and review criteria.
8. Define local-regeneration rules.

**Output requirements**  
Produce a Multi-Action Segment Chain, not one overloaded motion prompt.

---

# 7. Weak prompt

> Lumi notices the ball, walks over, bends, picks it up, turns to Pip, shows it, smiles, and the camera follows everything.

---

# 8. Diagnosis of the weak prompt

- Seven actions are combined.
- Camera behavior is vague.
- Prop and hand continuity are not tracked.
- Several emotional and orientation changes happen at once.
- Stable boundaries are missing.
- Local regeneration is impossible.
- The model may skip actions or invent transitions.

---

# 9. Improved prompt

Keep one locked eye-level medium-wide shot and divide the action:

- A→B: Lumi turns eyes and head toward the ball.
- B→C: Lumi takes two slow steps and stops beside the ball.
- C→D: Lumi bends and picks up the ball with both hands.
- D→E: Lumi straightens and turns her head toward Pip.
- E→F: Lumi raises the ball to chest height and shows it.

Use each approved ending frame as the next first frame. Preserve camera, lighting, identity, wardrobe, garden, ball design, and screen direction.

---

# 10. Expected output

- A complete action inventory.
- Stable boundary states.
- One action per segment.
- Continuity tracking across the chain.
- A local-regeneration plan.

---

# 11. Output-review checklist

- [ ] Every meaningful action has a segment.
- [ ] Each boundary is stable.
- [ ] The same boundary frame is reused.
- [ ] Camera and screen direction match.
- [ ] Hands and prop state are correct.
- [ ] Emotion changes gradually.
- [ ] No action is skipped.
- [ ] Failed segments can be isolated.

---

# 12. Common mistakes

1. Treating a multi-action shot as one segment.
2. Creating unstable halfway boundaries.
3. Changing the camera between segments.
4. Failing to track hands.
5. Allowing the prop to jump.
6. Using different boundary images for adjacent segments.
7. Changing emotion too quickly.
8. Regenerating the whole shot for one failure.

---

# 13. Fifteen-minute practical exercise

Create one Multi-Action Segment Chain for:

“Lumi enters the workshop, walks to the table, sits, opens a box, and removes a red card.”

1. List actions.
2. Create states A through F.
3. Define each segment.
4. Track camera, screen direction, hands, body, box, and card.
5. Define review criteria.
6. Define the local-regeneration rule.

---

# 14. Expected exercise result

One complete Multi-Action Segment Chain with reusable boundaries.

---

# 15. Short quiz and answers

### Question 1

Can one shot contain several segments?

### Answer

Yes.
### Question 2

What is a boundary state?

### Answer

A stable state between two actions.
### Question 3

Why reuse the same boundary image?

### Answer

To preserve continuity.
### Question 4

What should each segment contain?

### Answer

One primary action.
### Question 5

What is locally regenerated?

### Answer

Only the failed segment and affected boundary.


---

# 16. Completion checklist

- [ ] I identify overloaded actions.
- [ ] I create stable boundaries.
- [ ] I use one action per segment.
- [ ] I track body, props, camera, and emotion.
- [ ] I define local regeneration.
- [ ] I completed a Multi-Action Segment Chain.

---

# 17. Lesson output

**Primary lesson artifact:** Multi-Action Shots and Segment Chains — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
