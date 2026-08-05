# Module 10

## Lesson 35 of 40 — S2V Conditioning Pipeline

**Study time:** approximately 25 minutes  
**Practice time:** approximately 20 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- trace the complete Speech-to-Video conditioning pipeline;
- explain the separate roles of image, speech audio, text direction, and optional pose guidance;
- distinguish identity conditioning from performance conditioning;
- identify conflicting inputs;
- plan a clean S2V shot before generation;
- attribute common failures to image, audio, prompt, pose, temporal generation, or decoding.

---

## 2. Core S2V pipeline

The course defines the S2V workflow as:

```text
Reference image
+ speech audio
+ text prompt
+ optional pose video
→ speech-driven video
```

Each condition has a different responsibility.

| Condition | Primary responsibility |
|---|---|
| Reference image | Character appearance and initial visual state |
| Speech audio | Timing, rhythm, pauses, energy, vocal performance |
| Text prompt | Acting, expression, scene, and camera direction |
| Pose guidance | Optional broad body movement and posture |

The strongest workflow keeps these responsibilities clear and non-conflicting.

---

## 3. Reference image responsibility

The reference image establishes:

- face;
- hair;
- clothing;
- body appearance;
- initial pose;
- camera framing;
- background;
- lighting;
- visual style.

A high-quality image should have:

- clear face;
- correct anatomy;
- readable mouth area;
- no obstruction across the lips;
- stable background;
- suitable framing for gestures;
- no unwanted text;
- no conflicting subjects.

The image does not define exact mouth motion or guarantee identity throughout the clip.

---

## 4. Speech-audio responsibility

Speech audio supplies temporal performance information.

It contains:

- when speech begins;
- when speech ends;
- word rhythm;
- pauses;
- syllable timing;
- energy;
- pitch movement;
- emotional intensity;
- sustained sounds;
- silence.

The model can use these patterns to guide:

- mouth movement;
- head rhythm;
- expression timing;
- possible gesture timing;
- overall performance energy.

Audio is therefore not merely a transcript in sound form.

---

## 5. Text-prompt responsibility

The text direction should explain how the performance should look.

Useful categories:

- emotional tone;
- gesture size;
- gaze direction;
- body stability;
- camera behavior;
- background behavior;
- style;
- invariants.

Example:

```text
The character speaks warmly with a gentle smile and small natural head movements. Her shoulders remain relaxed. The camera remains stationary. Preserve her face, black hair, blue dress, and classroom background.
```

The text should not contradict the audio.

An energetic voice with a direction saying “completely motionless and emotionless” creates competing conditions.

---

## 6. Optional pose-guidance responsibility

Pose guidance can provide broad body-motion information such as:

- torso position;
- arm placement;
- hand movement path;
- head orientation;
- posture changes;
- gross gesture timing.

Pose guidance is useful when speech alone does not define enough body movement.

It can also create conflict if:

- pose body proportions differ from the reference image;
- pose timing disagrees with audio;
- hands move outside the available frame;
- gesture intensity contradicts the acting prompt;
- pose contains motion too complex for the character design.

Pose is guidance, not an absolute guarantee of anatomical accuracy.

---

## 7. Conditioning hierarchy

A practical hierarchy is:

```text
Image:
Who is performing and where?

Audio:
When and with what vocal energy?

Prompt:
How should the performance be acted and filmed?

Pose:
What broad body motion should be followed?
```

This hierarchy prevents prompts from trying to replace information already provided by another condition.

---

## 8. S2V internal pipeline map

```text
Reference image ─► visual encoding ─────┐
                                       │
Speech audio ───► audio features ──────┤
                                       ▼
Text prompt ────► text embeddings ─► conditioned video generator
                                       ▲
Pose guidance ─► motion features ──────┘
                                       │
                                       ▼
                              generated latent video
                                       │
                                       ▼
                                  VAE decoder
                                       │
                                       ▼
                               speech-driven video
```

This map supports failure attribution.

---

## 9. Identity conditioning versus performance conditioning

### Identity conditioning

Primarily comes from the reference image.

It answers:

- what does the character look like?
- what are the colors and proportions?
- what is the initial framing?

### Performance conditioning

Primarily comes from audio, text, and optional pose.

It answers:

- when does the character speak?
- how energetic is the delivery?
- what expressions and gestures occur?
- how does the body move?

A production error occurs when the team uses a weak identity image but expects audio to preserve the face, or uses clean audio but gives no acting direction and expects a precise emotional performance.

---

## 10. Audio duration and shot duration

The visible performance must cover the speech timeline.

If the audio is six seconds, the shot must provide enough video time for:

- initial expression;
- speech onset;
- sentence rhythm;
- pauses;
- final expression or settle.

Cutting the video shorter than the audio creates missing performance.

Extending video beyond the audio creates silent sections that still require controlled mouth and body behavior.

---

## 11. Framing for speech performance

Choose framing according to what matters.

### Close-up

Best for:

- lips;
- eyes;
- facial emotion.

Risk:

- facial drift becomes highly visible;
- small errors are obvious.

### Medium shot

Best for:

- face plus small hand gestures;
- natural upper-body performance.

Risk:

- hands add anatomical complexity.

### Wide shot

Best for:

- body performance;
- environment.

Risk:

- mouth detail becomes too small for careful lip review.

---

## 12. Input-quality checklist

### Reference image

- one clear subject;
- visible mouth;
- correct face;
- stable background;
- adequate empty gesture space;
- matching aspect ratio;
- no strong motion blur.

### Audio

- clear speech;
- low background noise;
- stable level;
- no clipping;
- correct final dialogue;
- deliberate pauses;
- appropriate emotional performance.

### Prompt

- one emotional direction;
- one camera behavior;
- controlled gesture size;
- explicit invariants;
- no conflict with audio.

### Pose

- correct timing;
- compatible body proportions;
- gestures inside frame;
- not excessively complex.

---

## 13. Practical shot plan

Shot:

```text
A seated teacher delivers one calm sentence.
```

### Image

Medium shot, clear face, hands visible at rest, simple classroom background.

### Audio

Six-second calm recording with one natural pause.

### Prompt

Warm expression, small head movements, one gentle hand gesture, fixed camera, stable background.

### Pose

Optional. Use only if a particular hand gesture is necessary.

This design minimizes competing motion and keeps review focused.

---

## 14. Expected result

A strong result should show:

- stable character identity;
- mouth movement aligned with speech activity;
- little or no mouth movement during silence;
- expression matching vocal tone;
- restrained head and hand movement;
- stable camera and background;
- natural settle after the sentence.

---

## 15. Failure attribution table

| Symptom | Likely input or stage |
|---|---|
| Face differs from reference | Image conditioning or temporal generation |
| Mouth moves during silence | Audio alignment or temporal generation |
| Performance is too energetic | Audio energy, prompt, or pose conflict |
| Hands leave frame | Pose or framing problem |
| Background warps | Camera conflict or temporal generation |
| Dialogue timing is correct but emotion is weak | Prompt or source expression |
| Mouth area is unclear | Reference image quality or framing |
| Gesture occurs before emphasis | Audio-pose temporal conflict |

---

## 16. Plain-language explanation

Think of S2V as directing an actor with four production documents.

- The image is the casting photo and set design.
- The audio is the exact spoken performance.
- The prompt is the director’s acting note.
- The pose guidance is optional choreography.

When these documents agree, the model receives a clear performance plan. When they disagree, the result may look unstable or confused.

---

## 17. Important terminology

| Term | Meaning |
|---|---|
| Reference image | Visual identity and starting-state condition |
| Audio condition | Speech timing and performance input |
| Acting direction | Text description of emotion and behavior |
| Pose guidance | Optional broad body-motion condition |
| Identity conditioning | Information defining who the subject is |
| Performance conditioning | Information defining how the subject acts over time |
| Input conflict | Conditions requesting incompatible behavior |
| Framing | Camera composition determining visible subject area |
| Settle | Small natural resting motion after an action or sentence |

---

## 18. Short quiz

1. Which input primarily defines identity?
2. Which input primarily defines speech timing?
3. What should the prompt define?
4. Is pose guidance required for every S2V shot?
5. Why must the mouth be clear in the reference image?
6. What happens if pose timing conflicts with audio emphasis?
7. Which framing is strongest for facial review?
8. Why should audio be final before generation?

---

## 19. Quiz answers

1. The reference image.
2. Speech audio.
3. Acting, expression, gestures, camera, scene behavior, and invariants.
4. No.
5. The model needs a strong visual basis for reconstructing speech-related mouth motion.
6. Gestures may occur at the wrong time or appear unnatural.
7. Close-up, though it also exposes facial errors more clearly.
8. Changing audio changes the performance timeline and may require regeneration.

---

## 20. Completion checklist

- [ ] I can trace the S2V pipeline.
- [ ] I know the separate role of each condition.
- [ ] I can identify conflicting inputs.
- [ ] I can choose useful framing.
- [ ] I can prepare an S2V input checklist.
- [ ] I can attribute failures to image, audio, prompt, pose, or generation.
- [ ] I can plan a simple controlled speaking shot.
