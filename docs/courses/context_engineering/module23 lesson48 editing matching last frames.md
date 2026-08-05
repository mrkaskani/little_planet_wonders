# Module 23

## Lesson 48 of 72 — Editing Matching Last Frames

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Create a last frame by editing the approved first frame when possible.
- Change only the pose, expression, or prop state required by the action.
- Preserve camera, perspective, identity, location, lighting, and style.
- Create a Last-Frame Editing Prompt and Approved Keyframe Package.

---

# 2. Why it matters for children under five

Generating the last frame independently often creates identity drift, camera change, prop redesign, different lighting, altered background, or inconsistent scale. Editing from the approved first frame preserves more of the scene.

The last frame defines the exact ending state of the segment and often becomes the shared boundary for the next segment. It must therefore be stable, readable, and complete.

For children under five, the ending state should clearly show what changed. If Lumi picks up the ball, the final frame should unmistakably show the ball in her hands and no longer on the ground.


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

## 1. Edit from first frame

Use the approved first frame as the base whenever the camera, location, wardrobe, and lighting should remain the same.

## 2. Required change

Define the smallest visual change needed: pose, hand position, expression, gaze, or prop state.

## 3. Ending state

The last frame should communicate completion. Do not stop in an unstable halfway pose.

## 4. Identity preservation

Face, hair, body proportions, clothing, colors, and material style remain unchanged.

## 5. Camera preservation

Keep shot size, height, perspective, framing, and lens relationship identical unless the shot intentionally changes camera.

## 6. Location preservation

Keep landmarks, furniture, barriers, weather, background props, and light direction fixed.

## 7. Prop transformation

Track the exact prop change: ground to hands, open to closed, empty to full, outside basket to inside basket.

## 8. Body mechanics

The ending pose should look balanced and physically possible. Avoid twisted limbs, floating objects, or impossible hand contact.

## 9. Shared boundary frame

A stable last frame may become the first frame of the next segment. It must support the next action.

## 10. Final usable frame

The best boundary may occur before the actual generated ending. During review, select the last stable usable frame.

## 11. Emotion continuity

Expression may change slightly when the action completes, but should not jump to a new unrelated emotion.

## 12. Local repair

If only hands or prop state are wrong, edit those elements rather than recreating the entire frame.


---

# 4. Practical example from the ongoing series

## Segment

Lumi picks up the red ball.

## First frame

- Ball on path
- Lumi standing left
- Hands empty
- Curious expression

## Last-frame changes

- Lumi bends slightly less after lifting
- Ball held with both hands at waist height
- Hands wrap around the ball clearly
- Ball removed from path
- Eyes remain on ball
- Expression remains curious with slight satisfaction

## Unchanged

- Face
- Hair
- Clothing
- Body proportions
- Camera
- Lighting
- Garden
- Basket positions
- Ball color, size, and material

This frame can become the first frame for the next “show the ball” segment.

---

# 5. Reusable context template

# Last-Frame Editing Plan

**Source first frame:**  
[Approved ID]

**Segment action:**  
[One action]

**Required ending state:**  
[Exact]

## Change

**Character pose changes:**  
[List]

**Expression changes:**  
[List]

**Eye direction changes:**  
[List]

**Hand or wing changes:**  
[List]

**Prop changes:**  
[Holder, location, orientation, state]

## Keep unchanged

- Character identity:
- Face and hair:
- Body proportions:
- Wardrobe:
- Camera:
- Perspective:
- Framing:
- Location layout:
- Landmarks:
- Lighting:
- Color:
- Weather:
- Background props:
- Visual style:

## Body and prop contact

- Hand placement:
- Weight and balance:
- Contact shadows:
- Prop scale:
- No floating:
- No duplication:

## Boundary use

**Will this frame start the next segment?**  
[Yes or no]

**Next action readiness:**  
[Description]

## Approval

- Action complete:
- Identity stable:
- Prop state correct:
- Camera match:
- Light match:
- Safe posture:
- Stable boundary:

---

# 6. Reusable prompt template

Edit the approved first frame into a matching last frame.

**Source**  
[Approved first-frame ID]

**One completed action**  
[Action]

**Ending state**  
[Exact visual result]

Change only:
- required body pose;
- required expression;
- eye direction;
- hand or wing position;
- prop holder, location, orientation, or state.

Keep unchanged:
- identity;
- face;
- hair;
- body proportions;
- wardrobe;
- camera;
- perspective;
- framing;
- location layout;
- landmarks;
- lighting;
- color palette;
- weather;
- visual style;
- unrelated props.

**Negative constraints**  
No extra character, no duplicate prop, no floating object, no camera change, no background change, no lighting shift, no new gesture, and no incomplete action.

**Output requirements**  
One stable completed last frame suitable as a segment boundary.

---

# 7. Weak prompt

> Generate a new image of Lumi after she picks up the ball.

---

# 8. Diagnosis of the weak prompt

- The last frame may be generated independently.
- Camera and composition may change.
- Identity and wardrobe may drift.
- Ball size, color, or material may change.
- Location layout and lighting are not protected.
- Hand contact and body balance are undefined.
- The frame may not connect to the first frame.

---

# 9. Improved prompt

Edit the approved first frame. Keep the exact camera, framing, perspective, lighting, Rainbow Garden layout, Lumi identity, wardrobe, body proportions, and ball design.

Change only Lumi’s pose and the ball state. End with Lumi holding the red ball with both hands at waist height. Remove the ball from the path. Keep her feet stable, body balanced, eyes on the ball, mouth closed, and expression gently curious.

No duplicate ball, no floating object, no hand distortion, no camera shift, no background change, and no extra gesture.

---

# 10. Expected output

- A matching last frame.
- Minimal controlled changes.
- Complete action and prop state.
- Stable identity, camera, location, and light.
- A usable shared boundary.

---

# 11. Output-review checklist

- [ ] The action is visibly complete.
- [ ] The last frame matches the first.
- [ ] Identity and wardrobe are stable.
- [ ] Camera and light are identical.
- [ ] Prop state is exact.
- [ ] Hands and body contact are plausible.
- [ ] No duplication or disappearance occurs.
- [ ] The frame supports the next segment.

---

# 12. Common mistakes

1. Generating the last frame from scratch.
2. Changing camera to improve composition.
3. Changing expression too much.
4. Leaving the original prop on the ground.
5. Using unstable hand contact.
6. Allowing background movement.
7. Choosing a distorted final frame as the boundary.
8. Failing to plan the next action.

---

# 13. Fifteen-minute practical exercise

Create two Last-Frame Editing Plans.

1. Pick up the ball.
2. Place the ball in the basket.

For each:
- identify the source first frame;
- define exact changes;
- define unchanged elements;
- define hand and prop contact;
- define boundary use;
- complete approval review.

---

# 14. Expected exercise result

Two matching last frames and an Approved Keyframe Package.

---

# 15. Short quiz and answers

### Question 1

Why edit from the first frame?

### Answer

To preserve identity, camera, location, lighting, and style.
### Question 2

What should change?

### Answer

Only elements required by the action.
### Question 3

What is a shared boundary frame?

### Answer

The ending frame of one segment used as the starting frame of the next.
### Question 4

Can the actual final generated frame be unusable?

### Answer

Yes. Select the last stable usable frame.
### Question 5

Why define prop contact?

### Answer

To avoid floating, duplication, or impossible holding.


---

# 16. Completion checklist

- [ ] I edit from approved first frames.
- [ ] I define minimal required changes.
- [ ] I protect identity, camera, location, and light.
- [ ] I verify prop and body contact.
- [ ] I plan shared boundaries.
- [ ] I completed an Approved Keyframe Package.

---

# 17. Lesson output

**Primary lesson artifact:** Editing Matching Last Frames — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
