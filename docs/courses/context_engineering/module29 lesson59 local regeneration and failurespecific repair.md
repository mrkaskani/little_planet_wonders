# Module 29

## Lesson 59 of 72 — Local Regeneration and Failure-Specific Repair

**Estimated study time:** 15 minutes  
**Estimated practice time:** 15 minutes

---

# 1. Learning objective

- Diagnose whether a failure comes from image, audio, prompt, motion, boundary, or editing.
- Repair only the smallest failed unit.
- Preserve approved neighboring assets and continuity.
- Choose between prompt revision, keyframe edit, audio regeneration, motion regeneration, trim, and replacement shot.
- Create a Failure and Regeneration Log.

---

# 2. Why it matters for children under five

Regenerating an entire scene because one hand failed wastes approved work and may create new continuity problems. Local regeneration keeps successful assets and repairs only the failed unit.

The first task is diagnosis. A wrong face may come from an incorrect first frame. A missing word comes from dialogue audio. A skipped action may come from an overloaded motion prompt. A jump between clips may come from mismatched boundaries. A rushed pause may come from editing.

A Failure and Regeneration Log records what failed, the likely cause, the repair unit, the new version, and the continuity checks required afterward.


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

## 1. Failure source

Classify the source: reference, first frame, last frame, audio, prompt, generation, continuity, or edit.

## 2. Smallest repairable unit

Repair the smallest asset that can solve the problem without changing approved work.

## 3. First-frame repair

Use when identity, pose, prop, camera, or background is wrong before motion begins.

## 4. Last-frame repair

Use when the intended ending state is incorrect or unstable.

## 5. Audio regeneration

Use when words, pronunciation, pace, emotion, or cleanliness fail.

## 6. Motion regeneration

Use when the boundaries are correct but the action path, timing, contact, or extra movement fails.

## 7. Prompt revision

Add or clarify only the instruction related to the observed failure.

## 8. Trim

Use when the useful action is complete and a defect exists only before or after it.

## 9. Replacement shot

Use when the planned shot is inherently too complex or unclear. Redesign the coverage instead of repeatedly forcing the same failure.

## 10. Neighbor preservation

Keep approved previous and next assets. Regenerated output must match their boundaries.

## 11. Regression review

After repair, check that the original failure is fixed and no new identity, prop, camera, safety, or continuity problem appears.

## 12. Version log

Record prompt, source assets, output, review, reason for rejection, and approved replacement.


---

# 4. Practical example from the ongoing series

## Failure

Lumi’s pickup clip has correct identity and camera, but the ball duplicates during the lift.

## Diagnosis

- First frame: correct
- Last frame: correct
- Prompt: prop contact not explicit enough
- Motion generation: duplication during transition

## Smallest repair

Regenerate only the pickup segment.

## Prompt revision

Add:
- The single red ball leaves the ground.
- Both hands maintain contact with the same ball.
- No second ball appears.
- The ground is empty after pickup.

## Regression review

Recheck hands, ball scale, mouth, camera, and final boundary.

---

# 5. Reusable context template

# Failure and Regeneration Log

**Episode, scene, shot, segment:**  
[IDs]

**Failed version:**  
[Version]

## Failure

**Observed problem:**  
[Specific]

**Frame or time range:**  
[Range]

**Impact:**  
[Usability, safety, continuity]

## Diagnosis

- Reference issue:
- First-frame issue:
- Last-frame issue:
- Audio issue:
- Prompt issue:
- Motion issue:
- Camera issue:
- Continuity issue:
- Editing issue:

**Most likely source:**  
[Source]

## Smallest repairable unit

[Asset or segment]

## Repair method

- Trim:
- First-frame edit:
- Last-frame edit:
- Audio regenerate:
- Motion regenerate:
- Prompt revise:
- Replacement shot:
- Edit change:

## Revised instruction

[Exact change]

## Protected approved assets

[List]

## New version

[Version]

## Regression review

- Original failure fixed:
- Identity:
- Prop:
- Camera:
- Mouth:
- Safety:
- Continuity:
- Boundary:
- Audio:

## Decision

[Approved or further repair]

---

# 6. Reusable prompt template

Diagnose a failed preschool production asset and recommend the smallest effective repair.

Use:
- approved references;
- source prompt;
- first and last frames;
- locked audio;
- Shot Review Sheet;
- Continuity Ledger;
- neighboring approved assets.

Identify:
- exact failure;
- time or frame range;
- likely source;
- smallest repairable unit;
- repair method;
- exact revised instruction;
- approved assets that must remain unchanged;
- regression-review checklist.

**Important rule**  
Do not regenerate a larger unit when a smaller repair can solve the problem.

**Output requirements**  
Produce a Failure and Regeneration Log.

---

# 7. Weak prompt

> Regenerate the whole scene until it looks right.

---

# 8. Diagnosis of the weak prompt

- The failure is not identified.
- Approved work may be lost.
- Each regeneration may introduce new drift.
- No source diagnosis exists.
- Continuity boundaries are not protected.
- Review cannot compare versions meaningfully.
- Time and creative effort are wasted.

---

# 9. Improved prompt

Identify the exact failed unit first.

The pickup segment duplicates the ball between 1.4 and 1.8 seconds. The approved first frame, last frame, camera, identity, and neighboring segments are correct.

Regenerate only the pickup segment. Clarify single-ball contact and empty-ground ending. Reuse the same approved boundaries. After generation, verify the original duplication is fixed and recheck hands, mouth, camera, identity, and continuity.

---

# 10. Expected output

- A specific failure diagnosis.
- The smallest repair unit.
- A targeted repair method.
- Preserved approved neighbors.
- A regression-review process.
- A versioned regeneration log.

---

# 11. Output-review checklist

- [ ] The failure is specific.
- [ ] The source diagnosis is reasonable.
- [ ] The repair unit is minimal.
- [ ] Approved assets are protected.
- [ ] Revised instruction targets the failure.
- [ ] Boundaries remain authoritative.
- [ ] Regression review checks new problems.
- [ ] Versions and decisions are recorded.

---

# 12. Common mistakes

1. Regenerating the entire scene.
2. Changing several instructions at once.
3. Repairing motion when the first frame is wrong.
4. Repairing video when audio wording is wrong.
5. Replacing approved boundaries unnecessarily.
6. Skipping regression review.
7. Failing to record versions.
8. Continuing to force a badly designed shot.

---

# 13. Fifteen-minute practical exercise

Complete four Failure and Regeneration Logs:

1. Wrong hairstyle in first frame.
2. Missing word in dialogue.
3. Duplicate prop during motion.
4. Good clip with pause shortened in editing.

Choose the smallest repair for each and write regression checks.

---

# 14. Expected exercise result

Four failure-specific repair plans and a reusable regeneration log.

---

# 15. Short quiz and answers

### Question 1

What is the first regeneration step?

### Answer

Diagnose the exact failure and source.
### Question 2

What should be repaired?

### Answer

The smallest effective unit.
### Question 3

When is audio regenerated?

### Answer

When wording, pronunciation, timing, emotion, or cleanliness fails.
### Question 4

Why perform regression review?

### Answer

To ensure the repair did not create new failures.
### Question 5

When should a shot be redesigned?

### Answer

When its planned structure is inherently too complex or unclear.


---

# 16. Completion checklist

- [ ] I diagnose failure sources.
- [ ] I choose the smallest repair unit.
- [ ] I preserve approved assets.
- [ ] I revise only relevant instructions.
- [ ] I perform regression review.
- [ ] I completed Failure and Regeneration Logs.

---

# 17. Lesson output

**Primary lesson artifact:** Local Regeneration and Failure-Specific Repair — completed planning document

Do not continue automatically. Continue only when the student requests the next lesson.
