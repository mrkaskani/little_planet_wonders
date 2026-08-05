# Module 22

## Lesson 45 of 72 — Negative Constraints and Prompt-Improvement Diagnosis

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Use negative constraints to prevent specific known failures.
- Diagnose vague, contradictory, overloaded, unsafe, and continuity-breaking prompts.
- Rewrite prompts using identity, context, one action, states, camera, emotion, continuity, safety, and output constraints.
- Create a Negative-Constraint Template and Prompt Diagnosis Sheet.

---

# 2. Why it matters for children under five

Positive direction explains what should happen. Negative constraints prevent predictable unwanted outcomes. They are especially useful when a production has already observed identity drift, extra objects, unwanted mouth movement, dangerous action, background changes, flicker, or emotional exaggeration.

Negative constraints should be specific and limited. A huge list of generic negatives can confuse the task or remove necessary behavior. The strongest constraints correspond to actual risks in the current shot.

Prompt diagnosis is a creative-review skill. Before generation, the student should identify missing identity, unclear state, too many actions, camera conflict, child-safety risk, and impossible continuity.


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

## 1. Positive instruction

States the desired result: Lumi gently reaches toward the red ball.

## 2. Negative constraint

States a specific failure to avoid: no extra ball, no wardrobe change, no mouth movement, no camera shake.

## 3. Risk-based negatives

Choose constraints based on the current output type and known failure history.

## 4. Identity negatives

Prevent hair, face, body, color, clothing, accessory, or voice changes.

## 5. Object negatives

Prevent extra props, duplication, disappearance, color changes, or impossible holder transitions.

## 6. Motion negatives

Prevent extra gestures, running, spinning, abrupt movement, frozen action, or incomplete ending.

## 7. Camera negatives

Prevent zoom, orbit, shake, rotation, reframing, or angle change when camera must remain locked.

## 8. Audio negatives

Prevent added words, repeated words, music, effects, other voices, shouting, or distorted pronunciation.

## 9. Child-safety negatives

Prevent frightening expressions, sudden loudness, unsafe imitation, aggressive movement, flashing, or prolonged distress.

## 10. Contradiction diagnosis

A prompt may request both locked camera and orbit, calm and explosive emotion, or fixed clothing and a new costume. Contradictions must be removed.

## 11. Overload diagnosis

Count primary actions, emotional changes, camera behaviors, and output goals. If several are present, divide the task.

## 12. Reviewable wording

Replace “make it better” with specific measurable corrections.


---

# 4. Practical example from the ongoing series

## Known failure

In a non-speaking clip, Lumi’s mouth moves as if speaking while she reaches for the ball.

## Useful negative constraints

- No speech.
- Mouth remains gently closed.
- No lip movement.
- No extra facial performance beyond gentle curiosity.
- No head turn after the reach begins.
- No additional hand gesture.
- No camera movement.
- No change to ball, clothing, or background.

These constraints respond directly to the observed failure.

---

# 5. Reusable context template

# Negative-Constraint Template

## Identity

- Do not change:
- Do not add:
- Do not remove:

## Character performance

- No unwanted mouth movement:
- No extra gesture:
- No emotional exaggeration:
- No unsafe movement:

## Props

- No duplication:
- No disappearance:
- No color or material change:
- No holder jump:

## Location

- No layout change:
- No extra objects:
- No background replacement:
- No lighting shift:

## Camera

- No zoom:
- No orbit:
- No shake:
- No angle change:
- No reframing:

## Audio

- No added words:
- No repeated words:
- No music or effects:
- No other voices:
- No shouting:

## Child safety

- No frightening imagery:
- No flashing or flicker:
- No dangerous imitation:
- No aggressive conflict:
- No sudden loudness:

# Prompt Diagnosis Sheet

**Task:**  
[What should be produced]

**Missing context:**  
[List]

**Contradictions:**  
[List]

**Too many actions:**  
[List]

**Continuity risks:**  
[List]

**Child-safety risks:**  
[List]

**Unclear output requirements:**  
[List]

**Recommended split:**  
[Segments or separate tasks]

**Rewritten prompt:**  
[Final]

---

# 6. Reusable prompt template

Diagnose and improve the following creative prompt.

Evaluate:
- missing identity;
- missing episode, scene, shot, or segment context;
- unclear starting or ending state;
- number of primary actions;
- contradictory camera instructions;
- unclear emotional intensity;
- continuity risks;
- object and wardrobe risks;
- audio risks;
- child-safety risks;
- vague output requirements;
- missing review criteria.

Then rewrite using:
- identity;
- context;
- one action;
- starting state;
- ending state;
- one camera behavior;
- emotion;
- continuity;
- safety;
- output constraints;
- specific negative constraints.

Use only negatives relevant to the current task.

---

# 7. Weak prompt

> Lumi picks up the ball, talks, turns, runs, shows it, laughs, and the camera moves dramatically, but keep everything the same and do not make mistakes.

---

# 8. Diagnosis of the weak prompt

- Several primary actions are combined.
- Speaking and non-speaking workflows are mixed.
- “Dramatically” conflicts with preschool comfort.
- “Keep everything the same” conflicts with several actions.
- Camera behavior is undefined and likely overloaded.
- Starting and ending states are missing.
- “Do not make mistakes” is not a useful negative constraint.
- Safety and review criteria are absent.

---

# 9. Improved prompt

Create one non-speaking controlled-action segment.

Starting state: Lumi stands beside the red ball with hands empty, mouth gently closed, and eyes on the ball.

Ending state: Lumi holds the ball with both hands at waist height.

Action: Lumi bends slightly and picks up the ball.

Camera: Locked eye-level medium-wide.

Emotion: Gentle curiosity.

Keep unchanged: identity, wardrobe, proportions, ball identity, garden layout, lighting, camera, and background.

Negative constraints: no speech, no lip movement, no running, no turn, no showing gesture, no laughter, no extra action, no camera movement, no extra ball, no prop disappearance.

Output: one complete pickup segment with stable beginning and ending frames.

---

# 10. Expected output

- A focused negative-constraint system.
- A diagnosis of missing and conflicting prompt elements.
- An overloaded action split into controlled tasks.
- Specific continuity and safety protection.
- A reviewable rewritten prompt.

---

# 11. Output-review checklist

- [ ] Negatives correspond to real risks.
- [ ] Positive direction remains primary.
- [ ] No generic giant negative list is used.
- [ ] Contradictions are removed.
- [ ] One action remains.
- [ ] Identity, prop, camera, and safety risks are protected.
- [ ] Output and review criteria are explicit.

---

# 12. Common mistakes

1. Using only negative instructions.
2. Adding every possible negative to every prompt.
3. Writing vague negatives such as “no mistakes.”
4. Failing to split overloaded actions.
5. Keeping contradictory positive and negative directions.
6. Using negatives to hide unclear starting state.
7. Forgetting child-safety constraints.
8. Not updating negatives after reviewing failures.

---

# 13. Fifteen-minute practical exercise

Diagnose three weak prompts.

For each:
1. Identify missing context.
2. Count actions.
3. Identify contradictions.
4. Identify continuity risks.
5. Identify safety risks.
6. Write five to ten relevant negative constraints.
7. Rewrite the prompt.
8. Add output and review criteria.

---

# 14. Expected exercise result

Three completed Prompt Diagnosis Sheets and one reusable Negative-Constraint Template.

---

# 15. Short quiz and answers

### Question 1

What is a negative constraint?

### Answer

A specific instruction preventing a known unwanted outcome.
### Question 2

Should negatives replace positive direction?

### Answer

No.
### Question 3

Why use risk-based negatives?

### Answer

They focus on likely failures without overloading the prompt.
### Question 4

What should happen to an overloaded prompt?

### Answer

Split it into controlled tasks or segments.
### Question 5

Is “do not make mistakes” useful?

### Answer

No. It is too vague.


---

# 16. Completion checklist

- [ ] I created a Negative-Constraint Template.
- [ ] I diagnose missing context.
- [ ] I identify contradictions and overload.
- [ ] I use risk-based negatives.
- [ ] I split complex actions.
- [ ] I completed Prompt Diagnosis Sheets.

---

# 17. Lesson output

**Primary lesson artifact:** Negative Constraints and Prompt-Improvement Diagnosis — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
