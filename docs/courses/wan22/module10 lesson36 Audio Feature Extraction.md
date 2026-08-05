# Module 10

## Lesson 36 of 40 — Audio Feature Extraction

**Study time:** approximately 25 minutes  
**Practice time:** approximately 20 minutes

---

## 1. Learning objective

By the end of this lesson, you should be able to:

- explain how speech audio becomes machine-processable features;
- distinguish waveform, sampling rate, audio frames, phonemes, prosody, rhythm, and energy;
- explain why audio contributes more than words;
- connect audio features to mouth, face, head, and body movement;
- diagnose input-audio problems before S2V generation;
- design a speech recording that supports stable video performance.

---

## 2. Audio as a waveform

A digital audio recording begins as a sequence of amplitude measurements over time.

Conceptually:

```text
quiet      speech peak      pause       speech
____/000\____/00\____
```

The waveform represents changing air pressure captured by a microphone.

The model does not understand the waveform as a human sentence directly. An audio-processing system converts it into feature representations that describe meaningful short-term patterns.

---

## 3. Sampling rate

The **sampling rate** is the number of waveform measurements captured per second.

A higher sampling rate represents faster acoustic changes with more measurement points.

Sampling rate affects:

- frequency detail;
- file size;
- compatibility;
- preprocessing;
- potential resampling.

The course goal is conceptual understanding rather than choosing one universal rate. The input should match the workflow’s expected format and should not be repeatedly converted without reason.

---

## 4. Audio frames

Audio is usually analyzed in short windows called **audio frames**.

Do not confuse them with video frames.

```text
Audio frame:
short segment of waveform used for acoustic analysis

Video frame:
one visible image in the video sequence
```

Speech changes quickly. Short windows help capture:

- vowel structure;
- consonant transitions;
- energy;
- pitch;
- silence;
- onset and offset timing.

Audio frames overlap or progress across the waveform to form a time sequence of features.

---

## 5. Acoustic features

An **acoustic feature** is a numerical description of a short part of the audio.

Features may encode information related to:

- frequency content;
- energy;
- pitch;
- voiced versus unvoiced sound;
- spectral shape;
- transitions;
- silence;
- rhythm.

The exact features and encoder architecture are model-specific. The course-level principle is:

```text
Waveform
→ short-time analysis
→ audio feature sequence
→ speech-driven video conditioning
```

---

## 6. Phonemes

A **phoneme** is a basic speech-sound category that helps distinguish words.

Examples in English include sound categories corresponding roughly to:

- “m”;
- “p”;
- “b”;
- “a”;
- “s.”

Different phonemes require different mouth configurations.

Examples:

- “m,” “p,” and “b” often involve closed lips;
- open vowels require a more open mouth;
- “f” and “v” involve contact between lower lip and upper teeth.

S2V does not need to display a linguistic label on screen. It needs audio representations that support appropriate time-varying mouth shapes.

---

## 7. Visemes

A **viseme** is a visually distinguishable mouth-shape category associated with one or more speech sounds.

Multiple phonemes can look similar on the lips.

Therefore:

```text
phoneme categories
≠
one unique visible mouth shape per sound
```

Lip synchronization is not simply matching every sound to one fixed drawing. Mouth shape also depends on neighboring sounds, speaking style, emotion, head angle, and coarticulation.

---

## 8. Coarticulation

**Coarticulation** means the mouth prepares for upcoming sounds and remains influenced by previous sounds.

The mouth shape for one phoneme changes depending on surrounding phonemes.

Example:

```text
sound A → sound B → sound C
```

The visible motion between shapes must be smooth. A model that switches between isolated mouth poses may look mechanical.

Temporal audio features help represent these transitions.

---

## 9. Prosody

**Prosody** describes how speech is delivered rather than only which words are spoken.

It includes:

- intonation;
- stress;
- rhythm;
- pitch movement;
- speaking rate;
- phrase boundaries;
- emotional emphasis.

The same words can produce different performances.

Calm:

```text
“We found the little blue bird.”
```

Excited:

```text
“We found the little blue bird!”
```

Prosody can influence:

- eyebrow movement;
- head movement;
- smile intensity;
- gesture size;
- body energy;
- pause behavior.

---

## 10. Rhythm and timing

Rhythm describes the pattern of speech activity and silence.

It includes:

- syllable timing;
- word spacing;
- pauses;
- phrase length;
- repeated beats in singing or chanting.

A useful conceptual timeline:

```text
speech phrase
→ short pause
→ emphasized word
→ longer pause
→ final phrase
```

The video performance should reflect these events rather than moving continuously at one intensity.

---

## 11. Energy

Audio energy indicates loudness or intensity over short periods.

Higher energy may correlate with:

- stronger mouth opening;
- larger facial expression;
- faster head movement;
- larger gestures.

Lower energy may correlate with:

- smaller mouth movement;
- restrained expression;
- calmer body behavior.

These are learned correlations, not fixed rules. A skilled actor can speak loudly while remaining physically controlled, so text acting direction still matters.

---

## 12. Pitch and intonation

Pitch relates to perceived vocal frequency.

Intonation is the pattern of pitch movement over a phrase.

Rising intonation may suggest:

- question;
- uncertainty;
- anticipation.

Falling intonation may suggest:

- completion;
- confidence;
- calm conclusion.

A speech-driven model may use these patterns to shape expression timing and head rhythm.

---

## 13. Silence is a feature

Silence is not “no information.”

A pause communicates:

- mouth should close or rest;
- the character may breathe;
- expression may remain;
- gesture may settle;
- the next phrase is about to begin.

Unwanted mouth movement during silence is a key S2V failure.

The review must inspect quiet sections, not only spoken words.

---

## 14. Speech-to-motion correspondence

Audio features can influence different motion scales.

### Fine scale

- lips;
- jaw;
- cheeks;
- blinking;
- subtle expression.

### Medium scale

- head nods;
- gaze shifts;
- shoulder movement.

### Broad scale

- hand gestures;
- torso rhythm;
- pose changes.

The audio most directly constrains timing. Text and pose conditions can refine which broader motions should occur.

---

## 15. Audio-quality problems

### Background noise

May create uncertain acoustic activity during supposed silence.

### Clipping

Distorts peaks and can damage speech features.

### Reverberation

Smears timing and makes phoneme boundaries less clear.

### Inconsistent volume

Creates unstable performance intensity.

### Multiple speakers

Creates ambiguous identity and timing.

### Music under speech

Can interfere with acoustic feature extraction if the workflow expects clean dialogue.

### Incorrect transcript or missed words

The generated performance follows the supplied audio, not the intended script in your head.

---

## 16. Recording guidance

A strong speech input should have:

- one clear speaker;
- correct final wording;
- controlled background noise;
- no clipping;
- deliberate emotion;
- natural pauses;
- stable microphone distance;
- appropriate speaking speed;
- clean beginning and ending.

Do not record a neutral placeholder and expect the text prompt alone to create a deeply emotional vocal performance. The audio already contains the timing and energy of the acting.

---

## 17. Audio-feature pipeline diagram

```text
Waveform
   │
   ▼
Short audio frames
   │
   ▼
Acoustic representation
   ├── phonetic content
   ├── timing
   ├── energy
   ├── pitch
   ├── pauses
   └── prosody
   │
   ▼
Temporal audio features
   │
   ▼
S2V conditioning
   │
   ▼
Mouth, face, head, and body performance
```

---

## 18. Practical listening experiment

Record or select one sentence spoken in three ways:

1. calm;
2. excited;
3. sad or tired.

Do not focus only on the words.

Mark:

- speech start;
- strongest emphasis;
- pauses;
- energy peaks;
- pitch direction;
- sentence ending;
- expected head movement;
- expected facial expression;
- expected gesture size.

---

## 19. Expected result

The three recordings contain the same linguistic content but different performance features.

A strong analysis recognizes that S2V should not create identical acting for all three.

- calm audio should encourage restrained motion;
- excited audio may encourage faster, larger motion;
- sad or tired audio may encourage slower timing and reduced energy.

Text direction can constrain or refine the visible interpretation.

---

## 20. Failure analysis

### Mouth moves during background noise

The system may interpret noise as speech activity.

### Lip timing feels late

Possible alignment, preprocessing, or temporal-generation issue.

### Expression is emotionally weak

The recording may contain weak prosody, or the acting prompt may be too vague.

### Gestures are excessive

Audio energy and prompt may both encourage large motion.

### Pauses are ignored

Review audio cleanliness and temporal alignment.

### Fast speech produces unstable lips

Rapid phonetic transitions create a difficult temporal-detail problem.

---

## 21. Plain-language explanation

Audio is not only a list of spoken words. It is a performance timeline.

It tells the model when the mouth should move, when it should rest, where the voice becomes stronger, and how the sentence rises and falls. These patterns help the model build facial and body behavior around the speech.

---

## 22. Important terminology

| Term | Meaning |
|---|---|
| Waveform | Amplitude measurements over time |
| Sampling rate | Number of waveform samples per second |
| Audio frame | Short analysis window of sound |
| Acoustic feature | Numerical description of a short audio segment |
| Phoneme | Basic speech-sound category |
| Viseme | Visually distinguishable mouth-shape category |
| Coarticulation | Influence of neighboring sounds on mouth shape |
| Prosody | Intonation, stress, rhythm, and expressive delivery |
| Energy | Short-term intensity of the audio |
| Pitch | Perceived vocal frequency |
| Silence region | Time segment without speech activity |

---

## 23. Short quiz

1. Is an audio frame the same as a video frame?
2. What does prosody include?
3. Why do several phonemes share one viseme?
4. What is coarticulation?
5. Why is silence important?
6. What can clipping damage?
7. Does a transcript contain all performance information?
8. Why should the final emotional delivery be recorded before generation?

---

## 24. Quiz answers

1. No. It is a short sound-analysis window.
2. Intonation, stress, rhythm, pitch movement, rate, and phrase structure.
3. Different sounds can have visually similar mouth shapes.
4. Neighboring sounds influence the current mouth shape and transition.
5. It controls mouth rest, breathing, settling, and phrase boundaries.
6. Acoustic features and speech clarity.
7. No. It lacks timing, energy, pitch, pauses, and emotion.
8. The audio supplies the real timing and vocal performance that drive the video.

---

## 25. Completion checklist

- [ ] I can explain waveform and sampling rate.
- [ ] I can distinguish audio and video frames.
- [ ] I understand phonemes, visemes, and coarticulation.
- [ ] I can explain prosody, rhythm, energy, and pitch.
- [ ] I understand why silence matters.
- [ ] I can identify poor audio inputs.
- [ ] I can prepare a clean emotional recording.
- [ ] I can connect audio features to visible motion.
