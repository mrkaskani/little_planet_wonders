# Character voice profiles

Each character voice profile is stored at:

```text
src/lpw/context/projects/<project>/characters/<character>/voice-profile.yaml
```

The profile is the authority for the character's voice identity, performance
rules, emotional reference recordings, and continuity constraints.

## Reference structure

Every entry under `references` must be a mapping with its own recording text
and its own generation prompt. Do not use a bare audio path and do not reuse a
single generic prompt for every emotional state.

```yaml
references:
  neutral-friendly:
    path: audio-assets/voice-references/example/neutral-friendly.wav
    target_duration_seconds: 6-10
    artifact:
      status: approved
      method: selected-voice-design-identity
      seed: 123456
    text: >
      Hello! I'm Example.
      I'm glad you're here.
    prompt: >
      Generate a clean neutral-friendly reference for Example.
      Preserve the character's approved age, pitch, timbre, resonance,
      articulation, accent, and speaking rhythm. Use calm welcoming energy.

  curious:
    path: audio-assets/voice-references/example/curious.wav
    target_duration_seconds: 6-10
    artifact:
      status: approved
      method: base-cloned-from-neutral-friendly
      seed: 123557
    text: >
      Hmm... what could that be?
      Shall we take a closer look?
    prompt: >
      Generate a curious reference for the exact same speaker.
      Preserve identity while adding thoughtful pauses and light upward
      question intonation. Do not make the speaker anxious or frightened.
```

Required fields for every reference:

- `path`: destination of the approved clean WAV.
- `target_duration_seconds`: intended reference duration.
- `artifact`: approval status, generation method, and reproducible seed for the
  WAV currently installed at `path`.
- `text`: exact words spoken in that reference audio. This exact transcript is
  required when the Base model later clones the voice.
- `prompt`: direction written specifically for that emotional reference. It
  must restate the immutable speaker traits and describe only the permitted
  performance change.

## Required reference family

The classroom characters currently use five references, each with distinct
text and direction:

- `neutral-friendly`: baseline identity and everyday delivery.
- `happy-gentle`: controlled happiness without shouting or shrillness.
- `curious`: questioning intonation and thoughtful pauses.
- `mild-concern`: slightly reduced energy with mild caring concern.
- `reassuring`: slower, patient encouragement and quiet confidence.

All references for one character must sound like the same speaker. Emotional
state may alter pacing, energy, pauses, and intonation, but must not alter age,
accent, pitch range, timbre, resonance, or articulation identity.

## VoiceDesign and cloning workflow

Use VoiceDesign only to create identity candidates. Once a neutral candidate is
approved, store it at the reference's `path` and use Qwen3-TTS Base voice
cloning for later dialogue. Pass the corresponding reference `text` exactly as
`ref_text`; a mismatched transcript weakens voice cloning.

Yoyo and Riri already follow this per-reference structure:

- `characters/yoyo/voice-profile.yaml`
- `characters/riri/voice-profile.yaml`

Their approved files are installed only under these canonical directories:

```text
src/lpw/context/projects/riri-yoyo/audio-assets/voice-references/yoyo/
src/lpw/context/projects/riri-yoyo/audio-assets/voice-references/riri/
```

Each directory contains exactly `neutral-friendly.wav`, `happy-gentle.wav`,
`curious.wav`, `mild-concern.wav`, and `reassuring.wav`. Seed-bearing audition
filenames are renamed when approved; profiles must never point into `outputs/`
or a candidate batch. Superseded samples may be deleted after installation.

## Generate all references from a profile

The character shell scripts read `text` and `prompt` directly from every
reference in the corresponding profile. The model is loaded once per profile:

```bash
./scripts/qwen3_tts/generate_yoyo_references.sh
./scripts/qwen3_tts/generate_riri_references.sh
```

The contrast pipeline also reads each character's current
`references.neutral-friendly.prompt` directly from the profile. There are no
separate hard-coded Yoyo or Riri identity-prompt shell scripts to keep in sync.

Generate only one named reference when iterating:

```bash
./scripts/qwen3_tts/generate_yoyo_references.sh --reference curious
./scripts/qwen3_tts/generate_riri_references.sh --reference reassuring
```

Candidates are written under `outputs/qwen3-tts/candidates/<character>/` and
are never silently overwritten. Use `--force` to regenerate the same seeds.
After listening, approve each candidate into its profile path:

```bash
./scripts/qwen3_tts/approve_voice.sh yoyo curious \
  outputs/qwen3-tts/candidates/yoyo/curious-seed-272030.wav

./scripts/qwen3_tts/approve_voice.sh riri reassuring \
  outputs/qwen3-tts/candidates/riri/reassuring-seed-314563.wav
```

VoiceDesign can still drift between emotional references. Treat the generated
files as candidates and approve only a set that audibly retains one speaker
identity. For final dialogue continuity, use the approved neutral reference
with the Base-model cloning scripts.

The VoiceDesign API exposes stochastic talker sampling. The contrast command
records `temperature`, `top_p`, `top_k`, and `repetition_penalty` in every
immutable batch manifest so a run can be reproduced or resumed safely. Start
with the checkpoint defaults; increase temperature only in a new exploratory
batch because greater variety can also reduce naturalness and family cohesion:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate --samples 12 \
  --temperature 1.0 --top-p 1.0 --top-k 50
```

## Cosine contrast selection

For stronger Yoyo/Riri separation, generate multiple neutral candidates using
the same audition text. This removes wording as a comparison variable:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate --samples 8
```

Generation automatically runs speaker analysis after the batch completes and
writes `outputs/qwen3-tts/contrast-analysis/<batch-id>/voice-contrast.md`.
VoiceDesign is released from memory before WavLM is loaded. Use
`--skip-analysis` only when WAV generation without a report is intentional.

Every run creates an immutable directory under
`outputs/qwen3-tts/contrast-batches/<batch-id>/`. Candidate filenames are
never reused across batches, and the manifest records the shared text,
prompts, seeds, status, and output paths.

Pair ranking is multi-objective. Speaker-embedding distance carries 60 percent
of the shortlist score, pitch separation 15 percent, cadence separation 5
percent, within-character family cohesion 10 percent, and profile-direction
fit 10 percent. Direction fit checks that Riri is higher and slower than Yoyo.
This favors voices that differ across characters without selecting a random
identity outlier or a pair whose acoustics contradict the character profiles.
The score is only for ranking candidates within a comparable run; final
selection still requires blind listening for naturalness, age, and character
fit.

Ranking does not imply acceptance. By default, the analyzer rejects a batch
unless at least one pair has speaker cosine below `0.85`, a within-family versus
cross-character margin of at least `0.08`, median-pitch separation of at least
`0.35` octaves, and the expected higher/slower Riri direction. These defaults
encode the listening result that pairs near `0.90` cosine still sounded like
one speaker with altered delivery. A rejected batch must not be approved.

If repeated VoiceDesign batches are rejected, stop regenerating from the same
model. Obtain two independently sourced voices—separate performers, genuinely
different preset speakers, or different synthesis models—approve those as the
neutral references, and use the Base model only for cloning. Pitch shifting a
single source is not an independent identity and does not satisfy the gate.

After two neutral identities pass listening and contrast review, lock them at
their profile `neutral-friendly.path`. Generate the other emotional reference
auditions through the Base cloning model so VoiceDesign cannot silently choose
a new speaker for each emotion:

```bash
./scripts/qwen3_tts/generate_cloned_reference_auditions.sh
```

The immutable output batch records the neutral audio path, exact reference
transcript, SHA-256 identity, target text, and seed. These files remain
auditions until explicitly approved.

For a controlled two-batch comparison, name the batches and change the seed
offset:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate \
  --batch-id contrast-a --samples 8 --seed-offset 0

./scripts/qwen3_tts/voice-contrast.sh generate \
  --batch-id contrast-b --samples 8 --seed-offset 1000
```

If generation is interrupted, resume missing files without replacing completed
WAVs:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate \
  --batch-id contrast-b --samples 8 --resume
```

Speaker analysis uses Microsoft's WavLM speaker-verification checkpoint. Its
download is explicit and separate; the analyzer never downloads weights:

```bash
./scripts/qwen3_tts/voice-contrast.sh download-analyzer
```

The `generate` action then performs generation and analysis together. The
standalone `analyze` action remains available to rebuild a report:

```bash
./scripts/qwen3_tts/voice-contrast.sh analyze \
  --batch-dir outputs/qwen3-tts/contrast-batches/contrast-a
```

Reports are written to `outputs/qwen3-tts/contrast-analysis/<batch-id>/`, so
one batch's analysis never replaces another batch's report:

- `voice-contrast.md`: family consistency and the easiest ranked review list.
- `voice-contrast.json`: complete embeddings-derived and acoustic results.
- `cross-family-pairs.csv`: every Yoyo/Riri pair ranked by cosine similarity.

To compare families across two saved batches, map all four directories and use
a new report directory:

```bash
./scripts/qwen3_tts/voice-contrast.sh analyze \
  --family yoyo-a=outputs/qwen3-tts/contrast-batches/contrast-a/yoyo \
  --family riri-a=outputs/qwen3-tts/contrast-batches/contrast-a/riri \
  --family yoyo-b=outputs/qwen3-tts/contrast-batches/contrast-b/yoyo \
  --family riri-b=outputs/qwen3-tts/contrast-batches/contrast-b/riri \
  --report-dir outputs/qwen3-tts/contrast-analysis/a-vs-b
```

Lower cross-family cosine similarity indicates greater estimated speaker
contrast. Within-family cosine describes how tightly samples in one folder
cluster. The report also includes median fundamental frequency, spectral
centroid, duration, RMS level, F0 separation, and spectral separation.

Cosine ranking is a shortlist, not an automatic approval. Listen to the top
pairs and reject unnatural delivery, poor pronunciation, noise, or voices that
conflict with character canon. Approve the best pair and use Base cloning for
all later dialogue.

### Understanding `voice-contrast.md`

- Cross-family cosine: lower means the two candidate voices are estimated to
  have more different speaker identities.
- Within-family cosine: higher means candidates for one character cluster more
  consistently; a low value indicates prompt/seed identity drift.
- Contrast margin: mean within-family cosine minus mean cross-family cosine.
  Prefer a larger positive margin when comparing batches analyzed with the
  same model, audition text, and conditions.
- F0 separation: median pitch difference expressed in octaves. `0` is similar
  pitch, `0.5` is half an octave, and `1.0` is one octave.
- Spectral-centroid difference: a rough darker-versus-brighter measurement;
  noise and recording conditions can affect it.
- RMS dBFS: recording loudness, not speaker identity.

Cosine has no universal pass/fail threshold. Shortlist low-cosine pairs, then
listen blind and reject unnatural outliers. The chosen pair must satisfy the
Yoyo/Riri acoustic contrast table as well as the numerical ranking.

## Yoyo and Riri acoustic contrast

The two profiles use deliberate physical-acoustic opposites. Preserve these
traits in every emotional reference; do not soften them into shared generic
terms such as merely “young, warm, bright, and cute.”

| Dimension | Yoyo | Riri |
|---|---|---|
| Apparent age | Seven-to-eight-year-old impression | Four-year-old impression |
| Presentation | Unmistakably boyish; never girlish or androgynous | Clearly feminine |
| Pitch | Low natural prepubescent-boy pitch | Higher child pitch |
| Phonation | Firm modal voice with restrained pitch variation | Light, gentle voice with more melodic flow |
| Resonance | Grounded and chest-forward | Light head resonance |
| Timbre | Dry, lightly nasal, reedy, slightly rough-edged | Smooth, round, non-nasal |
| Articulation | Firm, punchy, crisp, staccato consonants | Soft-edged, connected consonants |
| Rhythm | Quick stop-start | Slower and flowing |
| Tone | Dry and direct | Gentle and lightly airy |
