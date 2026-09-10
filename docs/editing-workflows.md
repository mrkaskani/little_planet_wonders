# Editing workflows

## Stage 1: prepare

`prepare_automated_edit`:

1. Loads timeline, export rules, take weights, context, and continuity.
2. Validates media and immutable approvals.
3. Verifies generation/package identity and audio stems.
4. Scores takes using configured weights.
5. Records disabled analyzers as `not-run` rather than inventing results.
6. Writes a versioned prepared package under `edits/`.

## Stage 2: automate and review

`automate_scene_edit` selects the best valid take per shot, follows the scene's
preferred order, validates adjacency, creates independent video/audio events, and
renders a review proxy. It enters `awaiting-approval`.

`approve_edit_preview` records an immutable reviewer decision tied to the plan
hash. It does not alter source context.

## Stage 3: post edit

`post_edit_scene` validates structured timecoded review notes and writes a new
patch version. Provider-required cleanup, grading, subtitle, or repair work is
reported honestly and stops at `changes-requested`.

The planned visual repair loop uses Qwen VL as a reviewer and Wan 2.2 as the
replacement-segment generator. Qwen VL receives the rendered attempt, exact
frame-rate metadata, resolved scene context, approved references, continuity
anchors, and their hashes. It must return structured findings with the first and
last bad frame, evidence frames, violated context authority, severity,
confidence, and one bounded repair action. A free-form “bad frame” description
is not sufficient for automated routing.

Wan 2.2 does not overwrite the source attempt. The repair planner expands the
failed interval to stable, workflow-valid boundaries, carries forward the same
character, location, camera, prop, dialogue, and audio locks, and creates a new
segment attempt. The edit pipeline inserts that attempt only after technical,
semantic, boundary-continuity, and human review pass.

Qwen VL is responsible for visible identity, anatomy, motion, location, lighting,
composition, mouth behavior, and temporal continuity. Voice, dialogue, music,
ambience, and sound continuity require audio hashes, timeline checks, and
audio-aware analyzers; visual analysis alone must not claim those checks passed.
The complete review and repair contract is taught in
[Lesson 6 of the Creating Scenes crash course](courses/creating_scenes/lesson_06_qwen_vl_wan_repair_and_continuity.md).

For final production, the bounded repair loop continues through Practical-RIFE
2× interpolation, temporally chunked SeedVR2 restoration to explicit 1920×1080,
master/delivery encoding, and comparative Qwen3-VL QA. Model downgrade records,
immutable candidate rules, selective retries, and the final completion gate are
defined in the [production restoration pipeline](production-restoration-pipeline.md).

An approved edit with no pending notes can proceed through scene finalization:

- normalize compatible clips;
- assemble hard cuts;
- mix four audio stems;
- validate output;
- create delivery files;
- write context snapshot and checksum archive manifest;
- commit scene continuity only after success.

## Chained segments in the EDL

Approved extension segments create editorial events with source ranges, timeline
positions, predecessor links, and up to four overlap frames. Use a hard cut when
frames match; use a very short blend only when needed. Preserve ambience beneath
the boundary and avoid long crossfades that reveal duplicated motion.
