# Creating a project context

This guide builds a complete nested LPW project context step by step. It covers
project identity, characters, voice profiles, locations, visual direction,
cinematography, props, wardrobe, audio, continuity, sequences, scenes, shots,
dialogue, editing, and validation.

The finished context is immutable source material. Generated dialogue, renders,
approvals, edits, and continuity updates belong under `runtime/`, `renders/`,
`edits/`, or `archive/`, never inside the context directory.

For a complete working example, compare each step with the
[`classroom` project](../src/lpw/context/projects/classroom/).

## 1. Choose the context layout

LPW supports two complementary layouts:

- `src/lpw/context/projects/<project-id>/` is the nested production layout used
  for project identity, character and location resources, voice and audio
  production, inheritance, editing, and export. This guide uses that layout.
- `src/lpw/context_data/` is the normalized story compiler layout. Use it when
  working directly with `ContextCompiler.compile_scene()` and the normalized
  project/story/scene/shot schemas described in [Context system](context-system.md).

By default, the nested context root is `src/lpw/context`. To keep context in a
different directory, set `CINEMATIC_CONTEXT_ROOT`; that directory must contain
`studio.yaml` or an equivalent studio context and a `projects/` directory.

Identifiers may contain letters, numbers, hyphens, and underscores. Lowercase
kebab-case is recommended. The examples below use:

```text
project:   moon-garden
character: lumi
location:  garden
sequence:  sequence-01
scene:     lantern-discovery
shot:      shot-001
```

## 2. Create the directory structure

Start with this structure. Add production-only files as the project grows.

```text
src/lpw/context/projects/moon-garden/
├── project.yaml
├── characters/
│   └── lumi/
│       ├── character.yaml
│       ├── voice-profile.yaml
│       ├── model-sheet.png
│       └── expression-sheet.png
├── locations/
│   └── garden/
│       ├── location.yaml
│       ├── exterior.png
│       └── floor-plan.png
├── visual_style/
│   ├── visual_style.yaml
│   ├── palette.yaml
│   └── lighting.yaml
├── cinematography/
│   └── camera-language.yaml
├── props/
│   └── moon-lantern.yaml
├── wardrobe/
│   └── lumi-primary.yaml
├── audios/
│   ├── audio.yaml
│   ├── audio_style.yaml
│   ├── voice-production.yaml
│   ├── pronunciation.yaml
│   ├── ambience.yaml
│   ├── sound-effects.yaml
│   ├── music.yaml
│   ├── mixing.yaml
│   └── audio-continuity.yaml
├── continuity/
│   └── initial-state.yaml
├── sequences/
│   └── sequence-01.yaml
├── scenes/
│   └── lantern-discovery/
│       ├── scene.yaml
│       ├── continuity-start.yaml
│       └── shots/
│           └── shot-001/
│               └── shot.yaml
├── episodes/
│   └── episode-001/
│       ├── dialogue-script.yaml
│       ├── sound-plan.yaml
│       └── music-plan.yaml
├── editing_style.yaml
└── export.yaml
```

The loader accepts `audio/` or `audios/`. This repository uses `audios/` for the
sample project. Character and location files can be flat, but the nested form is
preferred because it keeps their reference assets together.

## 3. Define the project

Create `projects/moon-garden/project.yaml`:

```yaml
id: moon-garden
type: project-context
version: 1
extends:
  - cinema://studio/cinematic-defaults@1

project:
  id: moon-garden
  title: Moon Garden
  genre: gentle animated adventure
  tone:
    - curious
    - warm
    - reassuring

visual_direction:
  realism: stylized-3d
  motion: calm and readable
  acting: expressive but restrained
  overall_style: soft handcrafted miniature world

technical:
  aspect_ratio: "2.39:1"
  frame_rate: 24
  generation_resolution: "1280x720"
  final_resolution: "1920x804"

consistency_rules:
  - preserve character identity
  - preserve wardrobe between connected shots
  - preserve location geometry
  - preserve approved colors and lighting direction
```

Keep the top-level `id` and `project.id` identical. Increment `version` whenever
an approved source context changes, then update every URI that inherits it.
`@latest` is intentionally rejected because it would make outputs
non-reproducible.

## 4. Define each character's visual identity

Create one visual character context per character, for example
`characters/lumi/character.yaml`:

```yaml
id: lumi
type: character-context
version: 1

identity:
  name: Lumi
  role: protagonist
  apparent_age: 4
  body_shape: small with rounded proportions
  skin: warm brown
  eyes: large dark-brown eyes
  hair: short dark curls
  permanent_feature: crescent-shaped hair clip above the left temple

performance:
  expression_style: clear and gentle
  gesture_style: one readable gesture at a time
  movement_style: calm walking, reaching, and pointing

reference_images:
  model_sheet: characters/lumi/model-sheet.png
  expressions: characters/lumi/expression-sheet.png

continuity_constraints:
  - preserve facial proportions and apparent age
  - preserve hair shape and crescent hair clip
  - preserve primary wardrobe unless a scripted change occurs
```

Reference images should be approved identity sheets, not arbitrary generations.
Use stable paths and descriptive keys such as `model_sheet`, `face_front`,
`face_three_quarter`, `profile`, `full_body`, and `expressions`.

Visual identity and voice identity are deliberately separate. A character can
exist without dialogue, and changing a voice profile must not silently change
the character's visual source of truth.

## 5. Define each character's voice

Create `characters/lumi/voice-profile.yaml`. The containing character directory
and `id` must match the character identifier:

```yaml
id: lumi

voice_identity:
  apparent_age: young child
  pitch: medium-high
  timbre: warm, light, and natural
  accent: neutral Persian
  speaking_speed: slow to moderate
  articulation: clear without sounding formal
  emotional_baseline: curious, friendly, and reassuring
  maximum_emotional_intensity: moderate

performance:
  pause_style: short natural pauses after questions
  vocal_energy: gentle and engaged
  default_volume: comfortable

generation:
  provider: externally-managed-local-tts
  voice_id: lumi-v1

references:
  neutral-friendly: audio-assets/voice-references/lumi/neutral-friendly.wav
  happy-gentle: audio-assets/voice-references/lumi/happy-gentle.wav
  curious: audio-assets/voice-references/lumi/curious.wav
  mild-concern: audio-assets/voice-references/lumi/mild-concern.wav
  reassuring: audio-assets/voice-references/lumi/reassuring.wav

consistency_constraints:
  - preserve vocal age, accent, warmth, and speaking speed
  - keep emotional performance readable but restrained
  - never shout directly at the audience
  - never use a reference as final dialogue unless its words match exactly
```

The repository does not install a text-to-speech model or download a voice. The
`provider` and `voice_id` identify an externally managed service. Reference WAVs
guide identity and emotion; they are not authoritative dialogue.

Use a different `voice_id` and clearly distinct identity description for every
speaking character. At minimum, provide `voice_identity`; LPW rejects a voice
profile that cannot resolve that section. For backward compatibility, LPW also
accepts `audios/voices/<character-id>.yaml`; a character-local
`voice-profile.yaml` takes precedence when both exist.

## 6. Define global voice-production rules

Create `audios/voice-production.yaml` for rules shared by every character:

```yaml
audience:
  minimum_age: 2
  maximum_age: 5

workflow:
  require_exact_approved_dialogue: true
  require_emotional_reference: true
  require_clean_dialogue: true
  require_review_before_lock: true
  require_locked_audio_for_lip_sync: true
  regenerate_video_after_material_audio_change: true

safety:
  maximum_emotional_intensity: 0.6
  require_reassuring_resolution: true
  forbidden_delivery:
    - screaming
    - aggressive shouting
    - extreme panic
    - sudden large volume changes

participation:
  minimum_response_pause_seconds: 3
  maximum_response_pause_seconds: 5
  avoid_distracting_motion_during_pause: true

lip_sync_input:
  dialogue_only: true
  forbid_music: true
  forbid_ambience: true
  forbid_foley: true
  forbid_sound_effects: true
```

LPW prepares instructions for external voice generation. Dialogue becomes
authoritative only after a real clean WAV is reviewed, its transcript exactly
matches the approved words, and all required review checks pass. Music,
ambience, Foley, and effects are mixed later and must not be baked into lip-sync
audio.

## 7. Define pronunciation and dialogue audio quality

Create `audios/pronunciation.yaml`:

```yaml
entries:
  Lumi:
    language: Persian
    phonetic: "loo-mee"
  MCP:
    language: English
    spoken_form: "M C P"

rules:
  - numbers must be expanded before voice generation
  - abbreviations must have an explicit spoken form
  - names must use dictionary pronunciation
  - pronunciation must remain consistent between scenes
```

Create `audios/audio_style.yaml`:

```yaml
dialogue:
  sample_rate: 48000
  bit_depth: 24
  channel_format: mono
  naturalism:
    preserve_breathing: true
    preserve_short_pauses: true
    avoid_robotic_timing: true
  timing:
    minimum_pause_between_sentences_ms: 250
    maximum_unplanned_silence_ms: 1000
  performance:
    acting_style: gentle naturalism
    match_scene_emotional_state: true
  lip_sync:
    generate_final_audio_before_video: true
    preserve_word_timing: true
    never_replace_audio_after_final_lip_sync: true
```

## 8. Define the master audio and mix

Create `audios/audio.yaml` for shared timeline and layer behavior:

```yaml
timeline:
  sample_rate: 48000
  channels: 2

dialogue:
  target_lufs: -16
  maximum_true_peak_db: -1
  noise_reduction: light
  compression: subtle
  preserve_breathing: true
  preserve_natural_pauses: true

music:
  dialogue_ducking_db: -6
  fade_in_ms: 400
  fade_out_ms: 600

ambience:
  continuous_room_tone: true
  crossfade_ms: 300
  avoid_sudden_environment_changes: true

sound_effects:
  realistic_distance: true
  match_room_acoustics: true
  avoid_exaggerated_impacts: true

speaker_profiles:
  lumi:
    dialogue_track: dialogue_lumi
    pan: 0
    eq_profile: lumi_dialogue_eq
```

Create `audios/mixing.yaml` for delivery limits and layer priority:

```yaml
technical:
  sample_rate: 48000
  delivery_channels: stereo
  maximum_true_peak_db: -1

loudness:
  web_target_lufs: -16
  cinematic_preview_lufs: -18

priority:
  - dialogue
  - important narrative sound effects
  - ambience
  - music
  - decorative sound effects

music:
  duck_under_dialogue: true
  ducking_db: -6
  attack_ms: 100
  release_ms: 500
```

## 9. Define locations and ambience

Create `locations/garden/location.yaml`:

```yaml
id: garden
type: location-context
version: 1
name: Moon Garden

architecture:
  layout: circular garden around a small central tree
  north: wooden gate
  south: covered activity table
  east: shallow flower beds
  west: tool shed

environment:
  weather: calm clear evening
  atmosphere: safe, quiet, and gently magical

lighting:
  key: warm moonlight from camera-left
  fill: soft lantern bounce
  practical: small amber path lights

continuity_constraints:
  - gate remains north
  - activity table remains south
  - tool shed remains west
  - central tree keeps the same shape and scale

reference_images:
  exterior: locations/garden/exterior.png
  floor_plan: locations/garden/floor-plan.png
```

Then create matching ambience in `audios/ambience.yaml`:

```yaml
locations:
  garden:
    base_layer:
      asset: audio-assets/ambience/garden-evening.wav
      loop: true
      gain_db: -26
    layers:
      - id: soft-leaves
        asset: audio-assets/ambience/soft-leaves.wav
        gain_db: -31
        loop: true
    continuity:
      preserve_across_cuts: true
      crossfade_ms: 400
      restart_on_every_shot: false
```

The key below `locations` must match the location `id`. Location geometry,
lighting direction, weather, ambience, and reference images should describe one
coherent place.

## 10. Define sound effects and music

Create `audios/sound-effects.yaml`:

```yaml
style:
  realism: recognizable and gently softened
  intensity: child-safe
  perspective_sensitive: true
  match_environment_acoustics: true

categories:
  props:
    moon_lantern:
      activate_asset: moon-lantern-on.wav
      deactivate_asset: moon-lantern-off.wav
  footsteps:
    garden:
      surface: soft stone path
      asset_set: soft-shoes-stone
      variation_policy: round-robin

rules:
  - use sound only for a visible or narratively required source
  - match distance, material, and position
  - preserve quiet space during participation pauses
  - dialogue always has priority
```

Create `audios/music.yaml`:

```yaml
identity:
  genre: [warm acoustic, playful melodic]
  instrumentation:
    primary: [marimba, soft piano, gentle flute]
  forbidden: [horror music, harsh impacts, chaotic percussion]

tempo:
  default_bpm: 72

themes:
  lumi:
    motif: three warm piano notes followed by a rising flute phrase
    instruments: [soft piano, gentle flute]
  discovery:
    motif: two light marimba notes and a warm sustained chord

mixing:
  dialogue_ducking_db: -6
  maximum_music_true_peak_db: -3

continuity:
  reuse_approved_themes: true
  preserve_motif_identity_across_instrument_variations: true
```

Use stable theme names in episode music plans. Do not let music reveal an answer
during an audience-response pause.

## 11. Define visual style and camera language

Create `visual_style/visual_style.yaml`:

```yaml
realism: stylized-3d
surface_style: soft handcrafted materials
shape_language: rounded and readable
detail_level: low to moderate
forbidden:
  - photorealistic skin
  - high-frequency background clutter
  - frightening shadows
```

Create `visual_style/palette.yaml`:

```yaml
palette:
  dominant:
    moon_blue: "#506A9E"
    leaf_green: "#537A5A"
    warm_amber: "#D79A4A"
  neutral:
    cream: "#F1E5CA"
    charcoal: "#34373D"
rules:
  - preserve natural skin tones
  - use warm amber for safe discoveries
  - avoid oversaturated colors
```

Create `cinematography/camera-language.yaml`:

```yaml
camera_language:
  establishing:
    lens: 24mm
    movement: locked or very slow crane
  character_medium:
    lens: 50mm
    height: eye-level
    movement: restrained tracking
  emotional_closeup:
    lens: 85mm
    movement: locked or very slow push-in
```

If `visual_style/lighting.yaml` is used, put project-wide lighting rules there.
Location-specific lighting belongs in each location context, and scene-specific
changes belong in the scene.

## 12. Define props and wardrobe

Create `props/moon-lantern.yaml`:

```yaml
moon_lantern:
  id: moon-lantern
  name: Moon Lantern
  category: safe-light
  visual_identity:
    primary_color: warm-amber
    material: frosted-glass-and-wood
    shape: small rounded lantern
    distinctive_features:
      - crescent cutout on each side
      - short blue carrying handle
  default_state:
    holder: none
    condition: inactive
    visibility: visible
  continuity_rules:
    preserve:
      - crescent cutouts
      - blue handle
      - size and material
    forbidden_changes:
      - changing color without a scripted event
      - changing holder without a transfer action
```

Create `wardrobe/lumi-primary.yaml`:

```yaml
lumi_primary:
  id: lumi-primary
  character_id: lumi
  name: Lumi Primary Wardrobe
  items:
    - id: yellow-cardigan
      type: cardigan
      visual_identity:
        color: muted-yellow
        material: knitted-cotton
        distinctive_features: [three wooden buttons]
    - id: blue-trousers
      type: trousers
      visual_identity:
        color: desaturated-blue
  continuity_rules:
    preserve:
      - cardigan color and buttons
      - trouser color
    forbidden_changes:
      - unexplained clothing replacement
      - unexplained dirt or damage
```

Files under `props/` and `wardrobe/` are merged into the project context. Give
each file a unique top-level key, as shown above, so multiple files do not
overwrite one another during the directory merge.

## 13. Define initial continuity

Create `continuity/initial-state.yaml`:

```yaml
visual_state:
  time_of_day: evening
  weather: clear

characters:
  lumi:
    wardrobe_id: lumi-primary
    emotional_state: curious
    position: beside the garden gate
    held_objects: []

locations:
  garden:
    gate_state: closed
    lantern_state: inactive

audio_state:
  music_position_seconds: 0
  ambience_position_seconds: 0
```

Source continuity describes the approved starting state. Runtime actions write
new versioned state outside this directory. Never edit source continuity to
pretend that an unreviewed generation was approved.

## 14. Define a sequence and scene

Create `sequences/sequence-01.yaml`:

```yaml
id: sequence-01
type: sequence-context
version: 1
extends:
  - cinema://projects/moon-garden@1

sequence:
  title: Lantern discovery
  scene_order: [lantern-discovery]
  dramatic_progression: curiosity to safe discovery

audio_chain:
  preserve_continuous_ambience: true
  preserve_music_position: true
```

Create `scenes/lantern-discovery/scene.yaml`:

```yaml
id: lantern-discovery
type: scene-context
version: 1
extends:
  - cinema://projects/moon-garden/sequences/sequence-01@1
imports:
  characters:
    - cinema://projects/moon-garden/characters/lumi@1
  locations:
    - cinema://projects/moon-garden/locations/garden@1

story:
  purpose: Lumi notices the unlit lantern and asks how to use it safely

emotional_arc:
  start: curiosity
  middle: mild uncertainty
  end: reassurance

environment:
  weather: clear
  time_of_day: evening

audio_chain:
  ambience:
    asset: garden-evening.wav
    restart: false
  music:
    cue: discovery
    continue_from_seconds: 0
```

The resolver supports pinned project, character, location, sequence, scene,
shot, and segment URIs. Imports load reusable contexts into a namespace; extends
builds the parent chain.

## 15. Define scene-start continuity and shots

Create `scenes/lantern-discovery/continuity-start.yaml`:

```yaml
id: lantern-discovery-start
type: continuity-state
version: 1

characters:
  lumi:
    look_direction: moon-lantern
    emotional_state: curious
    held_objects: []

location:
  gate_state: closed
  lantern_state: inactive

camera_state:
  side: south

audio_state:
  dialogue_position_seconds: 0
  music_position_seconds: 0
  ambience_position_seconds: 0
```

Create `scenes/lantern-discovery/shots/shot-001/shot.yaml`:

```yaml
id: shot-001
type: shot-context
version: 1
extends:
  - cinema://projects/moon-garden/scenes/lantern-discovery@1

shot:
  role: establishing-and-discovery
  duration_seconds: 5

camera:
  framing: medium-wide
  lens: 35mm
  height: child-eye-level
  side: south
  movement: very-slow-dolly-in

action:
  start: Lumi enters through the garden gate with empty hands
  end: Lumi stops at a safe distance and looks at the unlit lantern

generation:
  model: wan2.2-i2v-a14b
  segment_duration_seconds: 5
  require_approved_stable_end_frame: true
```

Each shot should state one clear start state, one clear end state, camera
geometry, duration, and the intended generation mode. Include every visible
character, prop state, wardrobe state, and continuity change either directly or
through inherited context.

For shots longer than a safe model segment, add segment files under
`shots/<shot-id>/segments/`. Every segment after the first should use the approved
predecessor end frame rather than inventing a new start frame.

## 16. Write exact dialogue and episode audio plans

Create `episodes/episode-001/dialogue-script.yaml`:

```yaml
episode_id: episode-001
language: fa
status: approved-text
lines:
  - scene_id: lantern-discovery
    shot_id: shot-001
    character_id: lumi
    exact_dialogue: "این چراغ چطور روشن می‌شود؟"
    primary_emotion: curious
    ending_emotion: curious
    emotional_intensity: 0.3
    speaking_speed: slow-to-moderate
    final_audio_status: not-generated
```

Create `episodes/episode-001/sound-plan.yaml`:

```yaml
episode_id: episode-001
scene_id: lantern-discovery
priority: [dialogue, visible-action sound, ambience, Foley, music]
cues:
  - cue_id: soft-gate-close
    category: environment
    source: garden gate
    action: gate settles closed after Lumi enters
    story_purpose: clarify the visible action
    volume: soft
    continue_across_cut: false
```

Create `episodes/episode-001/music-plan.yaml`:

```yaml
episode_id: episode-001
target_age: 2-5
emotional_goal: curiosity followed by reassurance
maximum_energy: moderate
scene_cues:
  - scene_id: lantern-discovery
    cue_id: lantern-discovery-theme
    action: start
    theme: discovery
    energy: low
    dialogue_relationship: duck-and-simplify
    continuity_into_next_scene: false
```

Approved dialogue text is the authority. Never silently rewrite it during voice
generation, lip sync, subtitle generation, or editing.

## 17. Add editing and export policies

At minimum, create `editing_style.yaml` with timeline and continuity rules:

```yaml
editing_identity:
  style: calm continuity-first editing
  emotional_priority: character performance
  continuity_priority: high

timeline:
  frame_rate: 24
  width: 1920
  height: 804
  resolution: 1920x804
  aspect_ratio: "2.39:1"
  audio_sample_rate: 48000
  pixel_format: yuv420p

cutting:
  default_transition: hard_cut
  dialogue:
    preserve_natural_pauses: true

continuity_rules:
  preserve_screen_direction: true
  preserve_eye_lines: true
  preserve_character_position: true
  preserve_prop_state: true
  preserve_wardrobe_state: true
```

Create `export.yaml` when finalization begins. Its frame rate, dimensions, aspect
ratio, and sample rate must agree with `project.yaml`, `editing_style.yaml`, and
the approved media. See the
[`classroom` export policy](../src/lpw/context/projects/classroom/export.yaml) for
review, web, master, and archive profiles.

## 18. Validate the project before production

Install the project, then run this read-only check from the repository root:

```bash
.venv/bin/python - <<'PY'
from lpw.audio.compiler import resolved_audio_context, resolved_voice_context
from lpw.context.chaining import ContextChainResolver
from lpw.context.loader import load_project_context

context = load_project_context(
    "moon-garden",
    character_ids=["lumi"],
    location_id="garden",
)
voice = resolved_voice_context("moon-garden", "lumi")
audio = resolved_audio_context("moon-garden")
scene = ContextChainResolver().resolve(
    "cinema://projects/moon-garden/scenes/lantern-discovery@1"
)

assert context["project"]["project"]["id"] == "moon-garden"
assert context["characters"][0]["id"] == "lumi"
assert context["location"]["id"] == "garden"
assert voice["generation"]["voice_id"] == "lumi-v1"
assert audio["audio"]["timeline"]["sample_rate"] == 48000
assert scene.context["id"] == "lantern-discovery"

print("context hash:", context["metadata"]["context_hash"])
print("scene hash:", scene.context_hash)
print("context chain:")
for item in scene.chain:
    print(" -", item["uri"])
PY
```

`load_project_context()` does not automatically discover all characters and
locations. Pass `character_ids` and `location_id`, or read their individual MCP
resources. This prevents a production request from accidentally pulling every
project asset into every shot.

With the MCP server running, inspect these resources:

```text
cinema://projects/moon-garden
cinema://projects/moon-garden/characters/lumi
cinema://projects/moon-garden/locations/garden
cinema://projects/moon-garden/audio
cinema://projects/moon-garden/voices/lumi
cinema://projects/moon-garden/voice-production
cinema://projects/moon-garden/sound-effects
cinema://projects/moon-garden/music
```

Then call `inspect_project_context` with the required characters and location,
and call `validate_context_chain` for the scene URI. These are read-only context
operations.

## 19. Pre-production checklist

- Every identifier uses only letters, numbers, hyphens, or underscores.
- Directory names, filenames, YAML IDs, dialogue character IDs, and voice IDs
  agree.
- Every inherited URI pins an integer version and resolves to an existing file.
- Project, editing, export, and generation frame rates and aspect ratios agree.
- Every speaking character has a visual context and a distinct voice profile.
- Every dialogue emotion resolves to a suitable reference, with a neutral
  fallback available.
- Exact dialogue, language, pronunciation, pace, pauses, and emotional intensity
  have been approved before generation.
- Voice-reference audio is clean and is not mistaken for final dialogue.
- Location geometry, reference images, lighting, and ambience describe the same
  physical space.
- Props and wardrobe have stable visual identity plus explicit forbidden changes.
- Scene-start continuity agrees with the previous approved state.
- Shot start and end states are concrete and do not overload one segment.
- Sound cues have visible or narratively required sources.
- Music ducks beneath speech and preserves participation pauses.
- Model-backed providers remain disabled until an operator verifies the external
  service and assets.
- Context inspection and chain validation pass before any render is submitted.
- Generated artifacts and approvals remain outside the source context tree.
