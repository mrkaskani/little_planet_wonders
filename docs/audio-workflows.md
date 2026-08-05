# Audio workflows

## Layer priority

1. Clean dialogue and narration
2. Essential visible-action sounds
3. Location ambience
4. Character and prop Foley
5. Music
6. Decorative effects

## Exact dialogue

`prepare_exact_dialogue` compiles permanent voice identity, emotional reference,
exact words, pronunciation, pauses, gestures, safety limits, and the expected WAV
name. It reports the provider as `not-run`.

`lock_exact_dialogue` requires:

- an existing WAV;
- a verified transcript exactly equal to the approved text;
- passing identity, accuracy, emotional-safety, and comfort checks;
- a named reviewer;
- a new immutable dialogue version.

The service copies the real WAV into versioned runtime storage and records its
SHA-256. `compile_dialogue_lip_sync_context` refuses unlocked audio and returns the
locked file/hash without invoking S2V.

## Dialogue-to-video

The S2V input contains clean locked dialogue. Music, ambience, Foley, and effects
are added during editing, not baked into lip-sync input. Material dialogue changes
require a new dialogue version and regenerated video.

## Ambience

Ambience is scene-level location identity. It normally continues across cuts,
does not restart on every shot, and preserves room tone beneath dialogue.

## Sound effects and Foley

`compile_sound_cue_sheet` validates source, visible action, story purpose,
material, timing, distance, position, volume, continuation, layer count, and
child-safety qualities. Participation pauses reject prominent effects.

Declared assets remain `declared-unverified` until execution confirms the file.
Missing assets remain `not-run`; LPW does not create fake sounds.

## Music

`compile_music_cue_sheet` maintains approved themes, validates energy and
instrumentation, ducks and simplifies beneath speech, and creates three-to-five
second participation spaces with no percussion, new melody, or answer reveal.

## Final mix

FFmpeg finalization resamples and mixes dialogue, music, ambience, and effects,
ducks music under dialogue, applies target loudness and true-peak rules, and keeps
dialogue centered. Final media is validated before continuity is committed.
