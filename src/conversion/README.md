# JSON cloned-conversation tool

For the complete workflow, JSON contract, output layout, timing behavior, and
troubleshooting guide, see
[`docs/cloned-conversations.md`](../../docs/cloned-conversations.md).

Generate a multi-character conversation from profile-locked neutral voices:

```bash
scripts/qwen3_tts/generate-conversation.sh conversation.json
```

Validate the JSON and all locked references without loading the model:

```bash
scripts/qwen3_tts/generate-conversation.sh conversation.json --validate-only
```

Minimal JSON contract:

```json
{
  "title": "Our Tiny Classroom Seed",
  "project": "classroom",
  "language": "English",
  "target_seconds": 30,
  "seed": 424242,
  "turns": [
    {"speaker": "yoyo", "text": "Riri, look! I found a tiny seed."},
    {"speaker": "riri", "text": "Do you think it could grow?"}
  ]
}
```

Each speaker resolves through:

```text
src/lpw/context/projects/<project>/characters/<speaker>/voice-profile.yaml
```

The profile's structured `references.neutral-friendly` entry supplies both the
locked WAV and its exact transcript. A turn may specify
`pause_after_seconds`; otherwise the assembler distributes pauses toward
`target_seconds`. Outputs are immutable and contain the combined WAV, per-turn
WAVs, transcript, and provenance manifest.
