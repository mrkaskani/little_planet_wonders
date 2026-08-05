# MCP reference

The server name is `Little Planet Wonders` and uses stdio transport.

## Resource groups

### Studio

- `cinema://studio`
- `cinema://studio/{profile}`
- `cinema://studio/editing-models`
- `cinema://studio/wan22`

### Project and creative identity

- `cinema://projects/{project_id}`
- `cinema://projects/{project_id}/characters/{character_id}`
- `cinema://projects/{project_id}/locations/{location_id}`
- `cinema://projects/{project_id}/audio`
- `cinema://projects/{project_id}/voices/{character_id}`
- `cinema://projects/{project_id}/voice-production`
- `cinema://projects/{project_id}/sound-effects`
- `cinema://projects/{project_id}/music`
- `cinema://projects/{project_id}/editing`
- `cinema://projects/{project_id}/post-editing`
- `cinema://projects/{project_id}/export`
- `cinema://projects/{project_id}/continuity`

### Story, scene, shot, and runtime

- `cinema://stories/{story_id}/scenes/{scene_id}`
- `cinema://projects/{project_id}/scenes/{scene_id}`
- `cinema://projects/{project_id}/shots/{shot_id}`
- `cinema://projects/{project_id}/scenes/{scene_id}/edit-context`
- `cinema://projects/{project_id}/scenes/{scene_id}/prepared-package`
- `cinema://runtime/{segment_id}/end-state`
- `cinema://runtime/{scene_id}/audio-state`
- `cinema://runtime/{scene_id}/editing-state`

## Tool groups

### Context and production planning

`compile_scene_context`, `get_scene_summary`, `build_scene_generation_plan`,
`plan_scene_production`, `inspect_project_context`, `resolve_context_chain`, and
`validate_context_chain` are local context operations.

### Generation

`compile_wan_shot`, `compile_dialogue`, and `compile_cinematic_shot` compile
packages. `generate_cinematic_video` controls real scene execution and should be
used only with deliberately enabled providers. `render_wan_i2v_shot` is the
specialized local ComfyUI I2V boundary.

### Render evidence

`create_render_attempt`, `validate_render_attempt`, `review_render_attempt`,
`approve_render_attempt`, `reject_render_attempt`, and `create_scene_release`
manage versioned evidence and decisions.

### Voice and audio

`prepare_exact_dialogue`, `lock_exact_dialogue`,
`compile_dialogue_lip_sync_context`, `compile_sound_cue_sheet`, and
`compile_music_cue_sheet` enforce exact words, clean audio, safety, and mix rules.

### Shot extension

`extend_cinematic_shot`, `compile_segment_context`, and `approve_segment` manage
short Wan segments and approved end-state continuity without enabling Animate.

### Editing and delivery

`create_edit_plan`, `validate_edit_plan`, `edit_cinematic_sequence`,
`save_continuity_state`, `approve_wan_render`, `prepare_automated_edit`,
`automate_scene_edit`, `approve_edit_preview`, `post_edit_scene`, and
`finalize_cinematic_scene` control the reviewed editing lifecycle.

Exact Python signatures and parameter descriptions are listed in
[Python API reference](api-reference.md).
