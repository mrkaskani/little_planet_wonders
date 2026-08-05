# Module 19

## Lesson 38 of 72 — Building Scene Cards, Shot Cards, and Segment Cards

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Turn an Episode Context Card into practical production cards.
- Define scene purpose, shot purpose, and segment change precisely.
- Classify every shot before generation.
- Create a Complete Episode Breakdown.

---

# 2. Why it matters for children under five

Cards make complex production visible and reviewable. A Scene Card explains the local story unit. A Shot Card explains what one camera view must communicate. A Segment Card explains exactly what one generation unit changes.

Without cards, teams often discover missing shots, inconsistent props, unclear audio, impossible transitions, or overloaded actions during generation. Planning cards are cheaper and safer to revise than finished media.


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

## 1. Scene Card

Records scene purpose, location, time, characters, starting state, ending state, learning beat, emotion, audio, and continuity.

## 2. Shot Card

Records shot number, purpose, classification, framing, camera, visible characters, props, dialogue, action, and review criteria.

## 3. Segment Card

Records exact start image, end image or audio, one action, allowed changes, unchanged elements, duration intention, and boundary continuity.

## 4. Shot purpose

Every shot should communicate something necessary: orientation, discovery, emotion, dialogue, action, participation, transition, or result.

## 5. Shot classification

Classify before generation: speaking-character, non-speaking controlled action, multi-action, complex performance, or environment.

## 6. Coverage

Coverage is the set of shots needed to understand and edit the scene. Include orientation, action, reaction, learning detail, and resolution where necessary.

## 7. Continuity fields

Track screen direction, prop holder, hand occupancy, clothing, expression, weather, light, background, and audio state.

## 8. Audio planning

Record locked dialogue needs, narration, ambience, Foley, effects, music, and silence before generation.

## 9. Review criteria

State what makes the card successful. This prevents approval based only on visual attractiveness.

## 10. Local regeneration

When a segment fails, keep approved cards and neighboring outputs. Revise only the relevant action, image, audio, or prompt.


---

# 4. Practical example from the ongoing series

## Scene Card — Rainbow Garden discovery

**Purpose:** Introduce the red ball and the matching problem.

**Starting state:** Lumi and Pip are putting away materials.

**Ending state:** Lumi holds the red ball and both baskets are visible.

**Learning beat:** Name red and compare choices.

**Emotion:** Calm curiosity.

## Shot Card — Shot 4

**Purpose:** Participation.

**Classification:** Speaking-character shot.

**Framing:** Eye-level medium-wide.

**Dialogue:** “Which basket matches the red ball?”

**Visible elements:** Lumi, Pip, red ball, red basket, blue basket.

**Audio:** Locked clean Lumi dialogue. Music stops during pause.

## Segment Card — Shot 5B

**Purpose:** Place the ball.

**Classification:** Non-speaking controlled action.

**Start:** Lumi holds ball above basket.

**End:** Ball rests inside basket; Lumi’s hands release.

**Action:** Slowly place the ball.

**Camera:** Locked.

---

# 5. Reusable context template

# Scene Card

**Scene ID and title:**  
[ID]

**Purpose:**  
[Story, learning, emotional]

**Location and time:**  
[State]

**Characters present:**  
[List]

**Props present:**  
[List]

**Starting state:**  
[Full state]

**Ending state:**  
[Full state]

**Learning beat:**  
[Concept]

**Emotional beat:**  
[Change]

**Participation:**  
[If any]

**Audio plan:**  
[Dialogue, ambience, Foley, music, silence]

**Continuity into next scene:**  
[List]

# Shot Card

**Shot ID:**  
[ID]

**Purpose:**  
[Reason]

**Classification:**  
[Speaking, action, multi-action, performance, environment]

**Framing:**  
[Wide, medium, close]

**Camera behavior:**  
[One]

**Visible characters and props:**  
[List]

**Starting composition:**  
[State]

**Ending composition:**  
[State]

**Dialogue or narration:**  
[Exact or none]

**Action:**  
[One shot-level action]

**Audio:**  
[Plan]

**Review criteria:**  
[List]

# Segment Card

**Segment ID:**  
[ID]

**Source shot:**  
[Shot ID]

**Starting state or frame:**  
[Exact]

**Ending state or frame:**  
[Exact]

**Primary action:**  
[One]

**Camera behavior:**  
[One]

**Elements allowed to change:**  
[List]

**Elements unchanged:**  
[List]

**Audio source:**  
[Locked dialogue or none]

**Boundary continuity:**  
[Previous and next]

**Failure risks:**  
[List]

**Approval criteria:**  
[List]

---

# 6. Reusable prompt template

Convert the approved Episode Context Card into Scene Cards, Shot Cards, and Segment Cards.

For every scene:
- define purpose;
- starting and ending state;
- learning and emotional beat;
- characters, props, audio, and continuity.

For every shot:
- define purpose;
- classify workflow;
- choose framing and one camera behavior;
- define visible elements;
- define dialogue, action, and review criteria.

For every multi-action shot:
- divide into segments;
- define exact starting and ending states;
- use one action per segment;
- state allowed and unchanged elements;
- define shared boundaries.

**Output requirements**  
Produce a Complete Episode Breakdown ready for reference creation, audio locking, generation, editing, and review.

---

# 7. Weak prompt

> Generate a few clips for each scene and decide later how they fit together.

---

# 8. Diagnosis of the weak prompt

- Shot purpose is undefined.
- Coverage may be incomplete.
- Dialogue may not match visual duration.
- Continuity and prop state are not planned.
- Shot workflows are not classified.
- Several actions may be overloaded into one clip.
- Editing problems are postponed until after generation.

---

# 9. Improved prompt

Create a Scene Card for every story unit, then a Shot Card for every camera view. Classify each shot before generation.

For speaking shots, attach exact locked dialogue. For controlled action, define first frame, last frame, and one movement. For multi-action, create A→B, B→C, and C→D Segment Cards.

Track camera, screen direction, prop holder, expression, light, audio, and boundary continuity. Generate only after the cards pass review.

---

# 10. Expected output

- Complete Scene Cards.
- Purposeful Shot Cards.
- Workflow classification for every shot.
- Controlled Segment Cards.
- Audio and continuity planning.
- Review and regeneration criteria.

---

# 11. Output-review checklist

- [ ] Every scene advances story or learning.
- [ ] Every shot has a purpose.
- [ ] Every shot is classified.
- [ ] Speaking shots use exact dialogue.
- [ ] Action segments contain one movement.
- [ ] Coverage includes setup, action, result, and reaction.
- [ ] Continuity fields are complete.
- [ ] Approval criteria are explicit.

---

# 12. Common mistakes

1. Generating before classification.
2. Creating shots without purpose.
3. Missing reaction or result shots.
4. Leaving audio for later.
5. Overloading segments.
6. Failing to track props and direction.
7. Approving cards because they sound cinematic rather than clear.

---

# 13. Fifteen-minute practical exercise

Create one Scene Card, five Shot Cards, and at least three Segment Cards.

1. Define the scene’s starting and ending state.
2. Define one purpose for each shot.
3. Classify every shot.
4. Add framing and camera.
5. Add dialogue or action.
6. Add audio plan.
7. Split one multi-action shot.
8. Add continuity and review criteria.

---

# 14. Expected exercise result

A Complete Episode Breakdown for one scene.

---

# 15. Short quiz and answers

### Question 1

What does a Scene Card describe?

### Answer

One local story unit and its state, purpose, audio, and continuity.
### Question 2

What must every Shot Card include?

### Answer

Purpose and workflow classification.
### Question 3

What must every Segment Card contain?

### Answer

One action, one camera behavior, exact start and end states.
### Question 4

Why plan audio on cards?

### Answer

Dialogue and sound affect duration, performance, and editing.
### Question 5

What supports local regeneration?

### Answer

Precise segment boundaries and approval criteria.


---

# 16. Completion checklist

- [ ] I created Scene Cards.
- [ ] I created Shot Cards.
- [ ] I classified every shot.
- [ ] I created Segment Cards.
- [ ] I added audio and continuity.
- [ ] I added review criteria.
- [ ] I completed a scene-level Episode Breakdown.

---

# 17. Lesson output

**Primary lesson artifact:** Building Scene Cards, Shot Cards, and Segment Cards — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
