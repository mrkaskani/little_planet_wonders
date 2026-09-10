# Audio workflows

## Two-phase scene rule

Phase 1 creates and approves dialogue, music, ambience, Foley, sound effects, and
the scene-reference image. Dialogue is divided into one clean WAV per speaker
turn. Music, ambience, Foley, and effects remain separate stems.

Phase 2 sends one approved scene or continuity frame and one speaker's locked
clean dialogue WAV to each Wan S2V unit. The combined multi-speaker conversation,
music, ambience, Foley, and effects are forbidden as S2V conditioning. They are
added during editing after the generated picture passes review. See the
[Phase 1](courses/creating_scenes/phase_01_create_audio_and_scene_reference.md)
and [Phase 2](courses/creating_scenes/phase_02_generate_s2v_and_final_mix.md)
course guides.

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

For a conversation, compile one S2V unit per speaker turn. The assembled
multi-speaker `conversation.wav` is a pacing and editorial reference, not valid
S2V conditioning. The first unit may use the approved Phase 1 scene image; later
units should inherit the previous approved stable end frame unless a reviewed cut
introduces a new approved start frame.

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
