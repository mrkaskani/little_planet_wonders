# Stable Audio 3 Medium on Apple Silicon

The local Stable Audio 3 pipeline uses the Medium diffusion transformer with
its matching SAME-L codec through the official MLX runtime:

```text
--dit medium --decoder same-l
```

Both soundtrack and sound-effect jobs use this pairing. Model weights are
managed outside the project under `/Users/oldowl/AI-Audio/stable-audio-3/` and
are never downloaded implicitly by generation commands.

Download or repair the Medium bundle explicitly with:

```bash
scripts/stable-audio-3-medium/download-model.sh
```

Generate one effect through the project orchestrator:

```bash
python3 scripts/orchestrator/audio_generator.py sfx \
  "soft wooden classroom door closing, isolated recording" \
  --seconds 3 \
  --seed 5152 \
  --output /absolute/path/to/door-close.wav
```

Regenerate the named classroom library:

```bash
python3 scripts/stable-audio-3-medium/generate-classroom-sfx.py --overwrite
```

The library generator reads the approved classroom sound-effect specification,
writes 44.1 kHz stereo PCM WAV files beneath
`src/lpw/context/projects/riri-yoyo/audio-assets/sound-effects/`, applies the
configured peak ceilings, and records prompts, seeds, durations, and checksums
under `src/lpw/context/projects/riri-yoyo/audio-assets/manifests/`.
