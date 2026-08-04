# Editing workflow rules

For every editing request:

1. Create the edit plan before invoking a renderer.
2. Load the project editing, color, camera, audio, and continuity context.
3. Match every shot to the selected reference shot.
4. Preserve screen direction, eye line, character state, props, weather,
   lighting, palette, dialogue loudness, and room tone.
5. Reject the timeline when validation reports a blocking error.
6. Save final continuity by project, scene, and edit version under `runtime/`.

Render integrations such as FFmpeg, Resolve, or Premiere consume an accepted
plan; they do not bypass context validation.
