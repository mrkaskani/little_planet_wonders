# Generate conversations from cloned character voices

The `src/conversion` feature turns an ordered JSON conversation into one WAV
while preserving each character's profile-locked voice. It generates every
turn with the local Qwen3-TTS Base model, writes the individual turn files, and
assembles them with controlled pauses.

## Prerequisites

Run commands from the repository root. The following must already exist:

1. The Qwen3-TTS runtime at `.venv-qwen3-tts/`.
2. The externally managed Base checkpoint at:

   ```text
   models/qwen3-tts/Qwen3-TTS-12Hz-1.7B-Base/
   ```

3. One structured voice profile for every speaker at:

   ```text
   src/lpw/context/projects/<project>/characters/<speaker>/voice-profile.yaml
   ```

4. A real locked neutral reference at the profile's
   `references.neutral-friendly.path`.

Install the runtime and Base model explicitly when missing:

```bash
scripts/qwen3_tts/setup.sh
scripts/qwen3_tts/download_base.sh
```

Runtime setup and model download are separate operations. Conversation
generation never downloads weights implicitly.

## How a speaker is resolved

For a JSON turn such as:

```json
{"speaker": "riri", "text": "Shall we look together?"}
```

the generator loads:

```text
src/lpw/context/projects/<project>/characters/riri/voice-profile.yaml
```

It then reads these two values:

```yaml
references:
  neutral-friendly:
    path: audio-assets/voice-references/riri/neutral-friendly.wav
    text: >
      Hello! I'm happy to see you.
      It's a lovely day.
      Shall we look around together?
```

The WAV supplies the speaker identity and `text` supplies its exact reference
transcript. The generator uses full Base-model cloning rather than creating a
new VoiceDesign identity. Do not edit the reference transcript unless the
words in the locked WAV also change.

## Conversation JSON format

Create a JSON file anywhere in the workspace. A complete example is:

```json
{
  "title": "Our Tiny Classroom Seed",
  "project": "riri-yoyo",
  "language": "English",
  "target_seconds": 30,
  "seed": 424242,
  "turns": [
    {
      "speaker": "yoyo",
      "text": "Riri, look! I found a tiny seed beside the window."
    },
    {
      "speaker": "riri",
      "text": "Do you think it could grow into a flower?",
      "pause_after_seconds": 0.4
    },
    {
      "speaker": "yoyo",
      "text": "Let's give it water and a sunny place."
    }
  ]
}
```

Top-level fields:

| Field | Required | Default | Meaning |
|---|:---:|---|---|
| `title` | No | `Conversation` | Human-readable transcript title. |
| `project` | No | `riri-yoyo` | Project containing character profiles. |
| `language` | No | `English` | Language passed to Qwen3-TTS. |
| `target_seconds` | No | `30` | Desired assembled duration, from 1 to 3600 seconds. |
| `seed` | No | `424242` | Non-negative base seed for reproducible turn sampling. |
| `turns` | Yes | — | Non-empty ordered list of spoken turns. |

Turn fields:

| Field | Required | Meaning |
|---|:---:|---|
| `speaker` | Yes | Character directory ID, such as `yoyo` or `riri`. |
| `text` | Yes | Exact words synthesized for this turn. |
| `pause_after_seconds` | No | Explicit pause after the turn, from 0 to 10 seconds. |

Speaker IDs are normalized to lowercase. They cannot contain `/` or `..`.

## Validate before generating

Validate the JSON and every referenced profile/WAV without loading the model:

```bash
scripts/qwen3_tts/generate-conversation.sh \
  scripts/qwen3_tts/dialogues/classroom-seed.json \
  --validate-only
```

A successful result lists each speaker's canonical WAV and SHA-256 hash, then
reports the turn count, speaker count, and target duration.

Validation fails when JSON is malformed, a speaker profile is absent, the
neutral reference is unstructured, the WAV is missing, or its path escapes the
project context.

## Generate the conversation

Run:

```bash
scripts/qwen3_tts/generate-conversation.sh \
  scripts/qwen3_tts/dialogues/classroom-seed.json
```

The Base model is loaded once. A clone prompt is prepared once per unique
speaker and reused for that speaker's turns. Every turn receives a stable seed
derived from the JSON `seed` and turn position.

By default, output is written to a new timestamped directory:

```text
outputs/qwen3-tts/cloned-conversations/<json-name>-<timestamp>/
```

Choose an explicit output directory when integrating with another pipeline:

```bash
scripts/qwen3_tts/generate-conversation.sh conversation.json \
  --output-dir outputs/qwen3-tts/cloned-conversations/episode-001-scene-003
```

Output directories are immutable. The command refuses to replace an existing
directory; choose a new versioned name instead.

Use a non-default externally managed Base-model directory when needed:

```bash
scripts/qwen3_tts/generate-conversation.sh conversation.json \
  --model-dir /absolute/path/to/Qwen3-TTS-12Hz-1.7B-Base
```

## Output files

Each generation directory contains:

```text
conversation.wav
transcript.md
manifest.json
turns/
  001-yoyo.wav
  002-riri.wav
  ...
```

- `conversation.wav` is the final mono conversation.
- `turns/*.wav` contains each uncombined cloned line for review or editing.
- `transcript.md` records the ordered speaker text.
- `manifest.json` records the input specification, model, reference paths,
  reference SHA-256 hashes, turn seeds, durations, pause calculation, and all
  output paths.

## Duration and pauses

`target_seconds` guides pause allocation; it does not time-stretch voices.
When a turn does not define `pause_after_seconds`, the assembler distributes
the remaining target duration across unspecified gaps. Automatic gaps are
limited to 0.12–0.65 seconds.

If synthesized speech alone is longer than the target, the result will also be
longer. Shorten the dialogue rather than accelerating child voices. If exact
editorial timing matters, set explicit pauses and review the duration recorded
in `manifest.json`.

## Review and continuity

Listen to the combined conversation and individual turns before using them in
production. Verify:

- every turn uses the intended character;
- pronunciation matches the JSON exactly;
- the two characters remain distinguishable;
- emotional delivery is safe and appropriate;
- no line is clipped or interrupted;
- pauses feel conversational.

The generator always clones the neutral reference because that file is the
profile's permanent identity anchor. Emotional reference files remain useful
for direction and review, but swapping identity references between turns can
introduce speaker drift.

## Troubleshooting

`voice profile not found`
: The JSON `project` or turn `speaker` does not match the context directory.

`locked voice reference is missing`
: Install the approved WAV at the exact profile `path`; do not point the
  profile at a temporary output batch.

`Qwen Base model is missing`
: Run `scripts/qwen3_tts/download_base.sh` or provide `--model-dir`.

`output directory already exists and is immutable`
: Choose a new output directory. Existing generation provenance is never
  overwritten.

Conversation exceeds `target_seconds`
: The speech itself is too long. Reduce words or split the conversation into
  scenes; the assembler deliberately does not speed up voices.

## Implementation locations

- `src/conversion/schema.py`: JSON validation.
- `src/conversion/profiles.py`: profile and locked-WAV resolution.
- `src/conversion/generator.py`: cloning, per-turn output, and assembly.
- `src/conversion/cli.py`: command-line interface and validation mode.
- `scripts/qwen3_tts/generate-conversation.sh`: Qwen virtual-environment wrapper.
