# Module 10

## Lesson 37 of 40 — Temporal Alignment in S2V

**Study time:** approximately 25 minutes  
**Practice time:** approximately 25 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- explain how audio time maps to video time;
- calculate frame positions for speech events;
- evaluate lip synchronization, pause timing, expression, and gesture synchronization;
- explain chunked generation and boundary risks;
- identify temporal drift and unwanted mouth motion;
- create a frame-aware S2V review worksheet.

---

## 2. Two synchronized timelines

S2V combines:

```text
Audio timeline
+
Video-frame timeline
```

The audio has continuous time measured in seconds.

The video displays discrete frames at a chosen FPS.

At 24 FPS:

```text
1 second = 24 frames
```

A speech event at 2.5 seconds occurs near:

```text
2.5 × 24 = frame 60
```

Temporal alignment means visible performance changes occur at appropriate positions relative to the audio.

---

## 3. Audio duration and video duration

The video must cover the complete audio duration.

Formula:

```text
Required frame count ≈ audio duration × FPS
```

Example:

```text
Audio duration: 6 seconds
FPS: 24
Required visible frames: approximately 144
```

A workflow may have model-specific frame constraints, but the conceptual relationship remains essential.

If the video is too short:

- final words are missing;
- mouth motion is cut off;
- sentence ending is abrupt.

If the video is much longer:

- silent tail must remain stable;
- mouth may move without speech;
- identity drift may accumulate.

---

## 4. Lip synchronization

Lip synchronization means mouth motion corresponds to speech timing.

Review dimensions:

- speech onset;
- consonant closures;
- vowel openings;
- phrase rhythm;
- pauses;
- sentence ending;
- absence of silent mouth motion.

Perfect lip synchronization is not only “mouth opens when sound exists.” Different sounds require different shapes and transitions.

---

## 5. Onset alignment

**Onset** is the beginning of a sound or phrase.

Common onset failures:

- mouth starts moving before the audio;
- mouth begins after the word starts;
- head gesture anticipates speech too early;
- first word occurs while the face remains static.

Review the first spoken sound carefully because early misalignment makes the complete performance feel detached.

---

## 6. Pause alignment

During a pause, the mouth should generally:

- close or move toward rest;
- stop speech-like articulation;
- preserve natural breathing;
- maintain emotional expression.

Unwanted behavior:

- repeated chewing motion;
- silent lip movement;
- random jaw opening;
- new gesture without audio or acting reason.

Pause review is one of the fastest ways to detect poor temporal alignment.

---

## 7. Ending alignment

At the end of speech:

- the final mouth shape should resolve;
- jaw should settle naturally;
- expression may remain;
- head or gesture may complete;
- video should not cut instantly unless the edit intentionally does so.

A small post-speech settle can make the result feel more natural, but a long silent tail increases drift risk.

---

## 8. Head and body rhythm

Speech-driven motion includes more than lips.

A natural performance may connect:

- head nod to emphasis;
- eyebrow raise to surprise;
- hand gesture to an important word;
- posture change to emotional shift;
- stillness to a pause.

A gesture that is perfectly animated but occurs on the wrong word is temporally incorrect.

---

## 9. Gesture synchronization

Use a simple event map.

| Time | Audio event | Desired visible event |
|---:|---|---|
| 0.0–0.5 | silence | calm resting pose |
| 0.5 | speech starts | mouth begins naturally |
| 1.8 | emphasized word | small hand gesture begins |
| 2.4 | pause | mouth rests, hand settles |
| 4.5 | final phrase | gentle head nod |
| 5.5 | speech ends | mouth closes, expression remains |

This helps evaluate whether performance events match the intended speech structure.

---

## 10. Temporal drift

Temporal drift means alignment becomes worse as the clip progresses.

Symptoms:

- first words align, later words do not;
- mouth gradually becomes early or late;
- gestures lose connection with emphasis;
- expression changes occur at arbitrary times.

Potential causes:

- long clip;
- chunk processing;
- timing mismatch;
- audio preprocessing changes;
- difficult fast speech;
- accumulated generation instability.

---

## 11. Chunked generation

Long audio may be processed in smaller temporal sections or chunks.

Conceptually:

```text
Audio/video segment 1
→ segment 2
→ segment 3
→ combined performance
```

Chunking reduces the amount of temporal context processed at once, but boundaries introduce risks.

---

## 12. Chunk-boundary failures

At a boundary, the next segment must continue:

- face identity;
- mouth state;
- head pose;
- body pose;
- gesture trajectory;
- background;
- lighting;
- camera framing.

Possible failures:

- face jumps;
- mouth resets;
- head position changes;
- gesture repeats;
- clothing shifts;
- lighting changes;
- one frame freezes or duplicates.

Avoid placing a boundary in the middle of a rapid word, large gesture, or head turn when possible.

---

## 13. Boundary placement strategy

Good candidate boundaries:

- natural sentence end;
- long pause;
- moment of stillness;
- edit point;
- change to a new camera shot.

Poor candidate boundaries:

- middle of a vowel;
- consonant closure;
- hand-object contact;
- fast head movement;
- emotional peak.

Production planning can reduce technical risk by aligning shot cuts with speech structure.

---

## 14. Frame-aware review

At 24 FPS, convert audio events to approximate frame positions.

Example:

| Audio time | Approximate frame |
|---:|---:|
| 0.5 s | 12 |
| 1.0 s | 24 |
| 2.5 s | 60 |
| 4.0 s | 96 |
| 6.0 s | 144 |

Use these positions to inspect:

- mouth onset;
- pause behavior;
- gesture timing;
- clip ending.

---

## 15. Slow-motion review

Normal playback is necessary for naturalness.

Frame-by-frame or slow playback is necessary for diagnosis.

Use both:

### Normal speed

Review:

- overall believability;
- emotional performance;
- rhythm;
- distraction.

### Slow or frame-level review

Review:

- early or late lip movement;
- mouth closure;
- sudden deformation;
- identity jumps;
- boundary discontinuity.

A video can look acceptable frame by frame but unnatural at normal speed, or the reverse.

---

## 16. Practical alignment experiment

Use a six-second sentence with:

- half-second silence before speech;
- one pause in the middle;
- one emphasized word;
- half-second settle after speech.

Create an event worksheet.

```text
Speech onset:
Pause start:
Pause end:
Emphasized word:
Speech end:
Settle end:
```

Convert each event to approximate frame numbers at 24 FPS.

Then review the generated result against those frames.

---

## 17. Expected result

A strong result should show:

- mouth starts near the first speech onset;
- speech-like articulation stops during the pause;
- expression follows the emphasized word;
- any gesture occurs near its intended emphasis;
- mouth resolves after the final sound;
- silent settle contains no random articulation;
- identity remains stable throughout.

---

## 18. Failure analysis table

| Symptom | Likely issue | First investigation |
|---|---|---|
| Mouth starts early | Onset alignment | Check leading silence and preprocessing |
| Mouth starts late | Temporal lag | Compare audio onset and first active frames |
| Mouth moves in pause | Silence handling | Inspect noise and pause region |
| Gesture occurs on wrong word | Audio-pose or prompt timing | Simplify gesture plan |
| Sync worsens over time | Temporal drift | Shorten or split clip |
| Face jumps at a boundary | Chunk continuity | Move boundary to pause or cut |
| Final word is cut | Duration mismatch | Increase frame coverage |
| Long silent tail drifts | Excess duration | Trim or use a shot cut |

---

## 19. Plain-language explanation

Temporal alignment is like matching an actor’s movements to a soundtrack.

The actor must start speaking at the right moment, rest during pauses, emphasize important words, and finish naturally. If the mouth is beautiful but half a second late, the performance still feels wrong.

---

## 20. Important terminology

| Term | Meaning |
|---|---|
| Temporal alignment | Matching visible performance to audio time |
| Onset | Beginning of a sound or phrase |
| Offset | End of a sound or phrase |
| Lip synchronization | Mouth motion matching speech |
| Temporal drift | Alignment error increasing over time |
| Chunk | Smaller temporal segment processed separately |
| Chunk boundary | Transition between generated segments |
| Gesture synchronization | Body movement timed to speech events |
| Silent tail | Video time remaining after speech ends |
| Settle | Natural movement returning toward rest |

---

## 21. Short quiz

1. How many frames represent six seconds at 24 FPS?
2. What is speech onset?
3. Why are pauses important for review?
4. What is temporal drift?
5. Why can chunk boundaries be visible?
6. Where should a boundary ideally occur?
7. Why use both normal-speed and slow review?
8. What should happen after the final word?

---

## 22. Quiz answers

1. Approximately 144 frames.
2. The beginning of speech activity.
3. They reveal unwanted mouth movement and poor silence handling.
4. Synchronization gradually becomes early or late over the clip.
5. Identity, pose, mouth, or background may not continue perfectly between separately processed segments.
6. At a natural pause, sentence end, still moment, or edit point.
7. Normal speed tests believability; slow review exposes exact timing and deformation.
8. The mouth should resolve and the performance should settle naturally.

---

## 23. Completion checklist

- [ ] I can map seconds to frames.
- [ ] I can inspect onset, pauses, and endings.
- [ ] I can evaluate gesture timing.
- [ ] I understand temporal drift.
- [ ] I can identify chunk-boundary failures.
- [ ] I can choose safer boundary positions.
- [ ] I can build a frame-aware review worksheet.
- [ ] I can recommend shortening or splitting a difficult clip.
