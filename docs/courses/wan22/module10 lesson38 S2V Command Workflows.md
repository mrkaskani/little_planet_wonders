# Module 10

## Lesson 38 of 40 — S2V Workflow Configurations

**Study time:** approximately 25 minutes  
**Practice time:** approximately 25 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- distinguish three major S2V workflow configurations;
- choose between existing audio, integrated voice generation, and audio-plus-pose guidance;
- identify the required inputs for each configuration;
- explain the production advantages and risks of each;
- plan validation checkpoints before video generation;
- create a configuration record without relying on implementation examples.

---

## 2. The three configurations

This lesson studies three conceptual S2V workflows:

1. existing recorded audio;
2. integrated voice-generation workflow;
3. existing audio with pose guidance.

All three use a reference image and acting direction. They differ in how speech and body motion are supplied.

---

## 3. Configuration A — Existing audio

```text
Reference image
+ final speech recording
+ acting prompt
→ speech-driven video
```

This is the clearest workflow when a final voice track already exists.

### Best use cases

- professional voice actor recording;
- approved dialogue timing;
- established emotional performance;
- multilingual recording already completed;
- precise editorial duration;
- audio created in a separate sound pipeline.

### Advantages

- exact final speech is known;
- timing can be reviewed before generation;
- audio can be cleaned and mastered;
- performance can be approved independently;
- easier synchronization with a final edit.

### Risks

- poor recording quality damages motion guidance;
- wrong words require regeneration;
- background noise may cause unwanted mouth activity;
- very fast speech may be hard to synchronize;
- long audio increases temporal drift risk.

---

## 4. Existing-audio preparation workflow

```text
Final script
→ voice performance
→ dialogue editing
→ noise cleanup
→ timing approval
→ reference-image approval
→ acting-direction approval
→ S2V generation
→ lip and identity review
```

The important principle is to finalize speech before generating expensive video candidates.

---

## 5. Configuration B — Integrated voice-generation workflow

```text
Reference voice example
+ reference transcript
+ new dialogue text
+ character image
+ acting direction
→ generated speech and speech-driven video workflow
```

This configuration creates or derives new speech from a voice reference and then uses it for the performance.

The course source identifies this as an integrated TTS workflow. The lesson focuses on production responsibilities rather than implementation commands.

---

## 6. Voice-reference responsibility

A voice-reference recording may communicate:

- speaker identity characteristics;
- accent;
- tone;
- pace;
- emotional style;
- vocal texture.

The reference transcript identifies what was spoken in the example so the voice system can separate voice characteristics from linguistic content.

The new dialogue text defines the words to be produced.

---

## 7. Integrated voice advantages

- rapid creation of new dialogue;
- consistent voice across iterations;
- easier script revision before final approval;
- useful when no final recording exists;
- enables a single workflow from text to voice to performance.

---

## 8. Integrated voice risks

- generated speech may mispronounce words;
- emotional delivery may be weaker than needed;
- punctuation may create unnatural timing;
- voice identity may vary;
- the generated duration may differ from the planned shot;
- speech errors become video-performance errors;
- a revised voice track requires S2V regeneration.

The speech output must be reviewed as audio before accepting the video.

---

## 9. Integrated workflow checkpoints

```text
New dialogue text
→ generate speech candidate
→ verify every word
→ review pronunciation
→ review pauses and emotion
→ approve duration
→ use approved speech for S2V
```

Do not review only the final lips. First confirm that the speech itself is correct.

---

## 10. Configuration C — Audio plus pose guidance

```text
Reference image
+ final speech audio
+ pose guidance
+ acting prompt
→ speech and pose-driven video
```

This configuration adds explicit broad body-motion guidance.

Use it when:

- a specific gesture is required;
- body rhythm matters;
- the character must follow planned choreography;
- audio alone produces weak or random gestures;
- repeated performances need similar body motion.

---

## 11. Pose-guidance advantages

- stronger control over broad body movement;
- more repeatable gesture timing;
- clearer performance blocking;
- reduced dependence on model-invented body motion;
- useful for matching a storyboard or performance reference.

---

## 12. Pose-guidance risks

- body proportions may conflict with the reference image;
- hands may move outside the frame;
- pose timing may disagree with speech;
- rapid pose changes may deform anatomy;
- gesture may overpower facial performance;
- pose may imply camera movement that does not exist;
- identity can drift during large body rotation.

Pose guidance increases control but also increases the number of conditions that must agree.

---

## 13. Choosing the configuration

| Production need | Recommended configuration |
|---|---|
| Final voice recording exists | Existing audio |
| Dialogue is still being created | Integrated voice workflow |
| Exact body gesture required | Audio plus pose guidance |
| Highest speech quality from actor | Existing audio |
| Rapid script variations | Integrated voice workflow |
| Minimal body complexity | Existing audio without pose |
| Choreographed speaking shot | Audio plus pose |

---

## 14. Configuration-selection questions

Ask in order:

1. Is the dialogue final?
2. Does an approved voice recording exist?
3. Is the emotional vocal performance acceptable?
4. Is a precise body gesture required?
5. Does the reference image provide enough gesture space?
6. Can the shot be shortened or split?
7. Which condition is allowed to control each aspect of performance?

---

## 15. Input-conflict matrix

| Conflict | Likely result |
|---|---|
| Calm audio + energetic pose | disconnected performance |
| Sad audio + cheerful prompt | unstable emotional expression |
| Close framing + wide arm gesture | hands leave frame |
| Side-facing image + frontal pose | body or identity deformation |
| Long speech + large movement | drift and synchronization difficulty |
| Noisy audio + silence requirement | mouth movement during pauses |

Resolve conflicts before generation.

---

## 16. Configuration record

For every S2V shot, record:

```text
Shot ID:
Configuration type:
Reference image version:
Audio source:
Audio duration:
Dialogue transcript:
Voice reference version, if applicable:
Pose source, if applicable:
Acting prompt version:
Target framing:
Target resolution:
Target FPS:
Seed:
Sampling settings:
Expected gestures:
Required invariants:
```

This makes results reproducible and reviewable.

---

## 17. Practical experiment

Use one short sentence and one character image.

Compare:

### Run A

Existing audio, no pose.

### Run B

Alternative generated voice, no pose.

### Run C

Existing audio with one controlled pose gesture.

Review:

- speech correctness;
- lip timing;
- emotional match;
- face identity;
- gesture timing;
- background stability;
- production complexity.

---

## 18. Expected result

Run A may provide the cleanest relationship between approved audio and facial performance.

Run B may support faster dialogue iteration but introduces voice-generation quality as an additional variable.

Run C may provide stronger body control but introduces pose compatibility and timing risks.

The best configuration is the simplest one that satisfies the shot requirement.

---

## 19. Failure analysis

### Existing audio: missed word

The error is already in the audio. Correct audio first.

### Integrated voice: wrong pronunciation

Approve and correct speech before video generation.

### Pose workflow: hand deforms

Simplify gesture, slow motion, or adjust framing.

### Pose workflow: gesture occurs too early

Pose timing conflicts with audio emphasis.

### All workflows: face drifts

Reduce duration, movement, rotation, or use a stronger reference image.

### All workflows: mouth moves in silence

Review background noise, pause structure, and temporal alignment.

---

## 20. Plain-language explanation

There are three ways to prepare a speaking character:

- give the model a finished recording;
- create a new voice from text and a reference;
- give it finished audio plus choreography.

Each extra input adds control, but also adds another opportunity for conflict. Start with the simplest workflow that can achieve the shot.

---

## 21. Important terminology

| Term | Meaning |
|---|---|
| Existing-audio workflow | Uses a completed speech recording |
| Integrated voice workflow | Creates new speech from text and voice reference information |
| Voice reference | Audio example defining desired speaker characteristics |
| Reference transcript | Text corresponding to the voice example |
| Pose-guided workflow | Adds broad body-motion guidance |
| Configuration record | Complete list of shot inputs and settings |
| Input conflict | Two conditions request incompatible behavior |
| Validation checkpoint | Review stage before expensive generation continues |

---

## 22. Short quiz

1. Which configuration is best when final actor audio exists?
2. What must be checked before using generated speech for video?
3. When should pose guidance be added?
4. Does more conditioning always mean a better result?
5. Why can calm audio and energetic pose conflict?
6. What is the safest workflow principle?
7. Why record the transcript with the shot?
8. What should happen after dialogue changes?

---

## 23. Quiz answers

1. Existing-audio workflow.
2. Words, pronunciation, timing, pauses, emotion, and duration.
3. When a specific broad body performance is required.
4. No. More conditions can conflict.
5. They describe different performance intensity and timing.
6. Use the simplest configuration that satisfies the requirement.
7. It supports verification, synchronization review, and reproducibility.
8. Regenerate or revalidate the audio and then regenerate the affected S2V shot.

---

## 24. Completion checklist

- [ ] I can explain all three S2V configurations.
- [ ] I can choose a configuration from production requirements.
- [ ] I can identify integrated-voice risks.
- [ ] I can identify pose-guidance risks.
- [ ] I can resolve condition conflicts before generation.
- [ ] I can create a complete configuration record.
- [ ] I understand why the simplest valid workflow is often best.
