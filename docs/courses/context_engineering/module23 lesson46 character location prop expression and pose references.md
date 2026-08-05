# Module 23

## Lesson 46 of 72 — Character, Location, Prop, Expression, and Pose References

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Plan a complete reference-image library before video generation.
- Create separate references for character identity, locations, props, expressions, poses, and wardrobe.
- Use references to approve first and last frames rather than sending uncontrolled collages into video generation.
- Create a Reference-Image Plan.

---

# 2. Why it matters for children under five

Video generation becomes less reliable when identity, location, prop, wardrobe, expression, and pose are not approved in advance. References reduce ambiguity by showing what the project already accepts.

Different references serve different purposes. A character sheet establishes identity. A location view establishes geography. A prop sheet establishes shape and material. An expression sheet establishes emotional limits. A pose sheet establishes body language.

A reference collage may help a human artist compare options, but a video model may interpret the collage as several panels, duplicate characters, or multiple objects. References should normally be used to create one approved first frame, not inserted as an uncontrolled scene image.


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

## 1. Reference hierarchy

Permanent references define identity. Task references define the current pose, expression, wardrobe, or state.

## 2. Character reference set

Front, side, three-quarter, back, full-body, close face, scale comparison, and approved wardrobe views.

## 3. Location reference set

Exterior, wide, reverse, entrance, activity area, learning area, safety boundary, lighting variations, and layout map.

## 4. Prop reference set

Front, side, scale, material detail, open or closed states, normal storage, and safe handling.

## 5. Expression reference set

Neutral-friendly, happy-gentle, curious, thinking, listening, mild concern, reassuring, asking for help, and calm celebration.

## 6. Pose reference set

Neutral standing, walking, looking, pointing, showing, listening, asking, helping, waiting, and placing.

## 7. Wardrobe reference set

Core outfit and approved variations from consistent angles.

## 8. Reference approval

A reference should be reviewed for identity, readability, safety, cultural respect, continuity, and small-screen clarity.

## 9. Reference naming

Use clear stable names and versions. Avoid “final2_new_best” style confusion.

## 10. Collage risk

A multi-panel sheet may be misread as multiple characters or a divided scene. Use it for planning and approval, then create a single scene frame.

## 11. Reference conflict

When two references disagree, do not average them. Resolve the conflict and approve one authoritative version.

## 12. Reference update

Only deliberate approved redesigns replace permanent references. Temporary episode states should not overwrite identity references.


---

# 4. Practical example from the ongoing series

## Lumi reference package

### Permanent identity

- Front full body
- Side full body
- Three-quarter full body
- Back view
- Face close-up
- Height comparison with Pip and Auntie Noura
- Core wardrobe reference

### Performance

- Expression sheet
- Pose sheet
- Showing-object pose
- Listening pose
- Asking-for-help pose

### Current episode

- Raincoat variation, if needed
- Wet-state reference, if needed
- Current prop-holder reference

The production uses these materials to create one clean approved scene frame.

---

# 5. Reusable context template

# Reference-Image Plan

## Character references

### Character
- Front:
- Side:
- Three-quarter:
- Back:
- Full body:
- Face close-up:
- Scale comparison:
- Core wardrobe:
- Approved variations:

## Expression references

- Neutral-friendly:
- Happy-gentle:
- Curious:
- Thinking:
- Listening:
- Mild concern:
- Reassuring:
- Asking for help:
- Calm celebration:

## Pose references

- Neutral:
- Walking:
- Looking:
- Pointing:
- Showing:
- Listening:
- Asking:
- Helping:
- Waiting:
- Placing:

## Location references

### Location
- Exterior:
- Wide:
- Reverse:
- Entrance:
- Activity area:
- Learning area:
- Safety boundary:
- Layout map:
- Lighting variations:

## Prop references

### Prop
- Front:
- Side:
- Scale:
- Material:
- Open or closed:
- Storage:
- Safe handling:

## Naming and versioning

[Convention]

## Approval status

- Draft:
- Reviewed:
- Revised:
- Approved:
- Locked:

## Collage-use rule

[Planning only unless a task explicitly requires a sheet]

## Conflict-resolution rule

[One authoritative approved reference]

---

# 6. Reusable prompt template

Create a Reference-Image Plan for a recurring preschool series.

Use approved Character, Expression, Pose, Wardrobe, Location, Prop, Visual, Color, Lighting, and Safety Bibles.

List the exact reference images needed for:
- character identity;
- scale;
- wardrobe;
- expressions;
- poses;
- locations;
- safety boundaries;
- lighting variations;
- props;
- safe handling;
- current episode-specific states.

For each reference:
- state purpose;
- state permanent or temporary status;
- define required angle;
- define approval criteria;
- define version and naming;
- identify possible conflict with other references.

**Important rule**  
Use reference sheets to create and approve single scene frames. Do not assume a multi-panel collage is suitable as direct video input.

**Output requirements**  
Produce a complete reference library plan and approval workflow.

---

# 7. Weak prompt

> Put all character poses, expressions, outfits, props, and locations into one collage and use it directly to generate the video.

---

# 8. Diagnosis of the weak prompt

- The collage may be interpreted as multiple panels or characters.
- Conflicting angles and states appear simultaneously.
- Permanent identity and temporary state are mixed.
- The scene composition is undefined.
- The model may duplicate props or merge outfits.
- No authoritative reference is selected.
- Video continuity becomes difficult to review.

---

# 9. Improved prompt

Maintain separate approved reference sets for character identity, expressions, poses, wardrobe, locations, and props.

For the current shot, select only the relevant references. Use them to create one clean first-frame scene image with one Lumi, one Pip if required, the correct wardrobe, one expression, one pose, the approved location, and the active props.

Review and approve the single frame before video generation. Do not use the full multi-panel collage as the scene input.

---

# 10. Expected output

- A complete reference library plan.
- Clear permanent and temporary status.
- Approved angle and scale coverage.
- Naming, versioning, and conflict-resolution rules.
- A controlled path from references to one scene frame.

---

# 11. Output-review checklist

- [ ] Identity references are complete.
- [ ] Location geography is covered.
- [ ] Props have scale and material references.
- [ ] Expressions and poses remain controlled.
- [ ] Wardrobe variations are approved.
- [ ] References do not conflict.
- [ ] Collages are not used as uncontrolled scene inputs.
- [ ] Approval status is recorded.

---

# 12. Common mistakes

1. Creating only front-view characters.
2. Using independently generated expression sheets with identity drift.
3. Skipping scale comparison.
4. Forgetting prop material and storage.
5. Using outdated location references.
6. Mixing permanent and temporary states.
7. Using a full collage directly as a scene.
8. Failing to name and lock versions.

---

# 13. Fifteen-minute practical exercise

Create a Reference-Image Plan.

1. List character identity views.
2. List scale and wardrobe views.
3. List expression and pose references.
4. List location views and layout.
5. List prop views and safe handling.
6. Add current episode references.
7. Create naming and versioning.
8. Define approval criteria.
9. Define collage-use and conflict-resolution rules.

---

# 14. Expected exercise result

A complete Reference-Image Plan ready for keyframe creation.

---

# 15. Short quiz and answers

### Question 1

What does a character reference sheet establish?

### Answer

Permanent identity, proportions, and approved views.
### Question 2

Why avoid direct collage input for video?

### Answer

It may be interpreted as multiple panels, characters, or states.
### Question 3

What happens when references conflict?

### Answer

Resolve the conflict and approve one authoritative version.
### Question 4

Should temporary state overwrite identity references?

### Answer

No.
### Question 5

What is the next step after selecting references?

### Answer

Create and approve one clean scene frame.


---

# 16. Completion checklist

- [ ] I planned character references.
- [ ] I planned location and prop references.
- [ ] I planned expression, pose, and wardrobe references.
- [ ] I created naming and approval rules.
- [ ] I defined collage-use restrictions.
- [ ] I completed a Reference-Image Plan.

---

# 17. Lesson output

**Primary lesson artifact:** Character, Location, Prop, Expression, and Pose References — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
