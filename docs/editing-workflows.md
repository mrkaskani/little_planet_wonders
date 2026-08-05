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
