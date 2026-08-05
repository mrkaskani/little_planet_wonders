# Module 22

## Lesson 43 of 72 — Permanent Context Versus Current Production Context

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Separate permanent project identity from episode, scene, shot, and temporary state.
- Understand which context should be inherited and which should be updated.
- Prevent temporary changes from rewriting character or world identity.
- Create a Context-Layer Map.

---

# 2. Why it matters for children under five

Prompt quality depends on giving the right context at the right level. Too little context creates drift. Too much unrelated context creates contradictions and overload.

Permanent context includes the audience, safety rules, series promise, world logic, character identity, visual style, voice identity, and recurring audio rules. Current production context includes what is true in this episode, scene, shot, or segment.

A raincoat is current wardrobe state, not a permanent redesign. Pip’s mild concern is a shot emotion, not a new personality. A ball inside the basket is an approved changed state for the end of the scene, not its starting state in every future episode.

This lesson creates a layered context system that later prompts can use consistently.


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

## 1. Permanent series context

Audience, educational philosophy, emotional promise, safety, recurring structure, visual identity, audio identity, and forbidden content.

## 2. Permanent character context

Appearance, proportions, personality, relationships, voice identity, movement identity, and approved knowledge history.

## 3. Permanent world context

World rules, fantasy limits, cause and effect, community, recurring locations, and safety boundaries.

## 4. Episode context

Learning goal, emotional goal, selected characters, active locations, weather, props, target vocabulary, problem, resolution, and planned continuity update.

## 5. Scene context

Local time, location, characters present, current emotion, active props, entering state, exiting state, and audio environment.

## 6. Shot context

Framing, camera, screen direction, visible elements, exact dialogue or action, starting composition, and ending composition.

## 7. Segment context

One controlled change: exact start state, exact end state, one movement, one camera behavior, allowed changes, and unchanged elements.

## 8. Temporary state

A condition true only now: wet coat, held ball, open gate, concerned expression, moved basket, evening light.

## 9. Approved changed state

A change deliberately carried forward: a repaired object, a learned concept, a relationship improvement, or a new recurring location feature.

## 10. Context inheritance

Lower levels receive relevant higher-level rules. A segment inherits identity and safety but does not need every historical detail.

## 11. Context conflict

When two instructions disagree, the prompt may produce drift. Permanent identity normally overrides accidental temporary variation.

## 12. Context update discipline

Only approved changes are written back into long-range continuity. Generated accidents are rejected, not stored.


---

# 4. Practical example from the ongoing series

## Permanent Lumi context

- Dark curly bob
- Coral overalls
- Curious and kind
- Warm childlike voice
- Gentle readable movement

## Episode context

- Learning red
- Rainbow Garden
- Light rain
- Yellow raincoat variation
- Red ball outside basket

## Scene context

- Rain has stopped
- Ground remains wet
- Lumi holds the ball
- Pip feels mildly unsure

## Shot context

- Eye-level medium-wide
- Lumi says, “Which basket matches?”
- Red and blue baskets visible

## Segment context

- Starting state: Lumi holds ball at chest height
- Ending state: Lumi lowers ball slightly while looking at baskets
- Allowed change: eyes, head, arms
- Unchanged: identity, clothing, background, light, basket positions

The layers stay specific without rewriting permanent identity.

---

# 5. Reusable context template

# Context-Layer Map

## Permanent series context

- Audience:
- Learning philosophy:
- Emotional promise:
- Safety:
- Visual style:
- Audio style:
- Recurring structure:
- Forbidden content:

## Permanent character context

### Character
- Appearance:
- Personality:
- Movement:
- Voice:
- Relationships:
- Approved knowledge:

## Permanent world context

- World rules:
- Fantasy limits:
- Cause and effect:
- Locations:
- Safety boundaries:

## Episode context

- Learning goal:
- Emotional goal:
- Characters:
- Locations:
- Weather and time:
- Props:
- Problem:
- Resolution:
- Vocabulary:
- Planned continuity update:

## Scene context

- Location:
- Time:
- Characters present:
- Current emotion:
- Current prop state:
- Starting state:
- Ending state:
- Audio environment:

## Shot context

- Purpose:
- Classification:
- Framing:
- Camera:
- Screen direction:
- Visible elements:
- Dialogue or action:
- Starting composition:
- Ending composition:

## Segment context

- One action:
- Starting state:
- Ending state:
- Allowed changes:
- Unchanged elements:
- Review criteria:

## Temporary state

[List]

## Approved changed state

[List]

## Update rule

[What may be written back into permanent continuity]

---

# 6. Reusable prompt template

Build a layered context package for one preschool production unit.

Separate:
1. permanent series context;
2. permanent character context;
3. permanent world context;
4. episode context;
5. scene context;
6. shot context;
7. segment context;
8. temporary state;
9. approved changed state.

For each item, state:
- where it belongs;
- whether it is inherited;
- whether it may change;
- who approves the change;
- whether it should be written into continuity.

**Output requirements**  
Produce a Context-Layer Map with no contradictory instructions.

**Review criteria**  
Temporary state must not rewrite identity. Generated accidents must not become approved context.

---

# 7. Weak prompt

> Put every detail from the entire project into every prompt and update the character whenever the output looks different.

---

# 8. Diagnosis of the weak prompt

- Every prompt becomes overloaded.
- Unrelated context may conflict.
- Generated drift is being treated as redesign.
- Temporary and permanent information are mixed.
- Changes have no approval process.
- Continuity will gradually degrade.
- Reviewers cannot identify which instruction has authority.

---

# 9. Improved prompt

Keep audience, safety, series identity, character identity, world rules, visual style, and voice identity as permanent context.

Add only the relevant episode, scene, shot, and segment context for the current task. Mark temporary state explicitly. State exactly what may change and what must remain unchanged.

If generation changes hair, clothing, layout, color, or identity without approval, reject the output. Do not update permanent context from accidental variation. Write back only deliberate approved changes.

---

# 10. Expected output

- A clear hierarchy of context.
- Relevant inheritance rules.
- Explicit temporary state.
- Approved change process.
- Conflict resolution and continuity-update rules.

---

# 11. Output-review checklist

- [ ] Permanent identity is clearly separated.
- [ ] Current context is specific.
- [ ] Temporary state is labeled.
- [ ] Allowed and unchanged elements are explicit.
- [ ] No layer contradicts another.
- [ ] Only relevant context is inherited.
- [ ] Generated errors are not stored.
- [ ] Approved changes have human authorization.

---

# 12. Common mistakes

1. Repeating all project information in every prompt.
2. Leaving temporary state unlabeled.
3. Treating a changed outfit as a redesign.
4. Updating context from one attractive output.
5. Failing to define authority between layers.
6. Using old scene state in a new scene.
7. Writing every episode detail into the Series Bible.

---

# 13. Fifteen-minute practical exercise

Create a Context-Layer Map for one shot.

1. List permanent series context.
2. List permanent character and world context.
3. Add episode context.
4. Add scene context.
5. Add shot context.
6. Add segment context.
7. Mark temporary state.
8. Mark one possible approved change.
9. Define update and rejection rules.
10. Check for contradictions.

---

# 14. Expected exercise result

A complete Context-Layer Map ready for master prompt construction.

---

# 15. Short quiz and answers

### Question 1

What is temporary state?

### Answer

A condition true only in the current production moment.
### Question 2

What is approved changed state?

### Answer

A deliberate change authorized to continue forward.
### Question 3

Should accidental drift update the Character Bible?

### Answer

No.
### Question 4

What does context inheritance mean?

### Answer

Lower levels receive relevant higher-level rules.
### Question 5

Which context normally has higher authority?

### Answer

Approved permanent identity and safety context.


---

# 16. Completion checklist

- [ ] I separated permanent and current context.
- [ ] I labeled temporary state.
- [ ] I defined approved changed state.
- [ ] I created inheritance rules.
- [ ] I created rejection and update rules.
- [ ] I completed a Context-Layer Map.

---

# 17. Lesson output

**Primary lesson artifact:** Permanent Context Versus Current Production Context — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
