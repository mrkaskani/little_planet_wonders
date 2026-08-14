# Qwen3-TTS 1.7B VoiceDesign and Base

The optional local runtime dependencies are declared in
`requirements.local.txt`. The setup script installs that file into the
dedicated `.venv-qwen3-tts` environment; these heavyweight ML dependencies are
kept separate from the core LPW package dependencies.

This project uses the official `qwen-tts` package and the Hugging Face
`Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` checkpoint. VoiceDesign generates speech
from target text plus a natural-language description of the desired voice,
emotion, and delivery.

The `Qwen/Qwen3-TTS-12Hz-1.7B-Base` checkpoint is also installed for rapid voice
cloning from reference audio and its exact transcript.

## Setup

The scripts create a dedicated Python 3.12 environment so the main LPW
environment is not changed.

```bash
scripts/qwen3_tts/setup.sh
scripts/qwen3_tts/download.sh
scripts/qwen3_tts/download_base.sh
```

The checkpoint is stored at:

```text
models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-VoiceDesign/
models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base/
```

The virtual environment and model weights are ignored by Git.

## Local web demo

```bash
scripts/qwen3_tts/launch_demo.sh
```

Then open <http://127.0.0.1:8000>. To choose another port:

```bash
QWEN_TTS_PORT=8001 scripts/qwen3_tts/launch_demo.sh
```

Launch the Base voice-cloning demo on a separate port:

```bash
scripts/qwen3_tts/launch_base_demo.sh
```

Then open <http://127.0.0.1:8001>. Override it with `QWEN_TTS_PORT` if needed.

The upstream examples target CUDA and recommend FlashAttention 2 on compatible
NVIDIA hardware. This Apple Silicon setup instead launches with `--device mps`,
`--dtype float16`, and `--no-flash-attn`. Generation may be substantially slower
than the published NVIDIA GPU examples.

`setup.sh` automatically installs `flash-attn` with a four-job build limit when
run on Linux with an available CUDA GPU. It safely skips that step on macOS/MPS,
where the official FlashAttention package is unsupported.

## Command-line generation

Generate a WAV by supplying target text and a description of the desired voice:

```bash
.venv-qwen3-tts/bin/python scripts/qwen3_tts/design_voice.py \
  --text "Welcome to our little planet." \
  --instruct "A warm, playful storyteller with a gentle pace." \
  --language English \
  --output outputs/qwen3-tts/voice-design.wav
```

The script uses the official `generate_voice_design` API. See the upstream model
card for current model details:

<https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign>

## Base voice cloning

Generate speech using a reference recording and its exact transcript:

```bash
.venv-qwen3-tts/bin/python scripts/qwen3_tts/clone_voice.py \
  --text "Welcome back to our little planet." \
  --ref-audio /absolute/path/to/reference.wav \
  --ref-text "The exact words spoken in the reference recording." \
  --language English \
  --output outputs/qwen3-tts/voice-clone.wav
```

This uses the official `generate_voice_clone` API:

<https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base>

## Locking distinct recurring character voices

VoiceDesign creates candidates; it does not guarantee that two prose prompts
will retain different speaker identities across later calls. Generate both
characters together with identical audition text through the contrast pipeline:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate \
  --batch-id contrast-a --samples 8 --seed-offset 0
```

This command generates the WAV batch and automatically writes its Markdown,
JSON, and CSV analysis under `outputs/qwen3-tts/contrast-analysis/contrast-a/`.

The generator reads each character's current `neutral-friendly.prompt`
directly from `voice-profile.yaml` at runtime. Yoyo and Riri therefore use the
new acoustic-opposite prompts without duplicated prompt text in shell scripts.
To audition another immutable candidate family, create another batch with a
different seed offset:

```bash
./scripts/qwen3_tts/voice-contrast.sh generate \
  --batch-id contrast-b --samples 8 --seed-offset 1000
```

Analyze and listen to the ranked files under the selected immutable batch.
When a candidate is approved, lock it as that character's neutral reference:

```bash
./scripts/qwen3_tts/approve_voice.sh yoyo \
  outputs/qwen3-tts/contrast-batches/contrast-a/yoyo/SELECTED.wav
./scripts/qwen3_tts/approve_voice.sh riri \
  outputs/qwen3-tts/contrast-batches/contrast-a/riri/SELECTED.wav
```

Generate later dialogue with the Base voice-cloning model so the approved WAV,
not a new VoiceDesign interpretation, supplies the speaker identity:

```bash
./scripts/qwen3_tts/speak_yoyo.sh "Let's look over here!" outputs/qwen3-tts/yoyo-line.wav
./scripts/qwen3_tts/speak_riri.sh "I'll come with you." outputs/qwen3-tts/riri-line.wav
```

The approval command refuses to replace an existing locked reference unless
`--force` is supplied after listening to the new candidate.
