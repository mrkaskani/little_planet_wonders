# Validation and approval

## Render attempts

`create_render_attempt` creates the next immutable `attempt-NNNN` directory and
stores media, attempt metadata, context snapshots, validation rules, and hashes.
Paths are constrained to render storage.

## Technical validation

Checks include:

- file existence and streams;
- dimensions, frame rate, duration, and pixel format;
- black segments and unintended freezes;
- audio stream/sample-rate/channel expectations;
- trim ranges and scene export compatibility.

Reports contain pass, warning, failure, and blocking issues. Tools such as
FFprobe/FFmpeg are invoked with argument arrays rather than shell strings.

## Semantic review

`review_render_attempt` records named checks such as identity, motion, location,
continuity, lip sync, audio consistency, safety, and editability. Review records
are evidence; they are not approval decisions.

## Approval and rejection

An attempt can receive one immutable approval or rejection. Approval verifies the
current package/context hashes and configured score thresholds. Rejection records
reviewer and reason without deleting evidence.

## Scene release

`create_scene_release` requires a current approved attempt for every scene shot.
It stores the final video and a release manifest with hashes and source approvals.
New releases use `release-NNNN`; existing releases are not overwritten.
