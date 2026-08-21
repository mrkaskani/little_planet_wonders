# Riri & Yoyo Pre-production TODO — Wan 2.2 Aligned

Scope: finish the reusable creative, visual, character, environment, audio, safety,
reference, and generation-policy foundations before story and production work begins.

This phase does not create episode stories, scripts, scene plans, shot prompts,
dialogue, renders, edits, or exports.

## Wan 2.2 operating contract

The project supports the four modes configured in `docs/wan22-setup.md`:

| Mode | Project model | Pre-production role |
| --- | --- | --- |
| T2V | `wan2.2-t2v-a14b` | Define reusable text-only environment and visual-language inputs where invention is acceptable. Do not depend on it for exact recurring character identity. |
| I2V | `wan2.2-i2v-a14b` | Prepare approved single-frame inputs for identity-, layout-, wardrobe-, prop-, and color-sensitive work. |
| TI2V | `wan2.2-ti2v-5b` | Prepare lightweight text or image draft inputs for testing composition, prompt clarity, and motion direction before A14B work. |
| S2V | `wan2.2-s2v-14b` | Prepare approved character frames and clean locked speech inputs for dialogue or vocal performance. |

Wan2.2-Animate-14B is part of the official model family but is deliberately
unsupported by this repository. Do not create Animate-specific performer-video,
replacement, mask, or relighting workflows unless the runtime policy is changed in
a separate approved task. Optional pose guidance remains valid for S2V when an exact
broad body gesture is necessary, but it is not a default requirement.

### Rules applied to every remaining task

- Give each recurring visible entity one canonical ID and one source of truth.
- Make identity depend on silhouette, main colors, proportions, and medium-sized
  features—not micro-detail, text, or dense patterns.
- Keep reusable prompt language ordered by subject and count, visible action,
  critical relationship, framing, environment, lighting, style, and short constraints.
- Prepare I2V and S2V source frames as one coherent image with correct anatomy,
  a clear silhouette, movement space, the intended aspect ratio, and no collage,
  watermark, labels, duplicate subjects, or accidental faces.
- Define motion as one observable action with direction, speed, scope, and a clear
  endpoint. Use one camera behavior and prefer controlled movement.
- Treat TI2V output as draft evidence for structure and motion, never as final
  approval evidence for face, fur, feathers, text, or fine material detail.
- Treat locked speech audio as S2V timing authority. Plan silence, speech onset,
  pauses, emphasis, and the final settle before video generation.
- Record model, task mode, prompt version, reference version, seed, dimensions,
  frame count, audio hash when applicable, and approval status for reproducibility.
- Keep generation-native dimensions and frame rate separate from the 1920×1080,
  24 fps delivery target; document any required crop, pad, upscale, or frame-rate
  conversion instead of assuming every mode generates the delivery format natively.

## Priority 0 — Lock project and model identity

- [x] Rewrite `project.yaml` for the Riri and Yoyo preschool project.
  - Define the genre, tone, audience, educational purpose, visual medium, and
    emotional-safety principles.
  - Confirm the canonical project and series names.
- [x] Remove the incompatible legacy thriller example context and its references.
- [x] Check that every pre-production YAML uses the same project identity,
  audience, tone, and terminology.
- [x] Lock the supported Wan 2.2 modes to T2V, I2V, TI2V, and S2V.
  - Keep Wan Animate disabled and rejected as required by `docs/wan22-setup.md`.
  - Do not download model weights or enable generation as part of pre-production.

Completion check: no active project file contradicts the preschool identity or
declares an unsupported Wan task.

## Priority 1 — Finish the Wan-readable visual foundation

- [x] Complete `visual_style/visual_style.yaml`.
  - Define medium, shape language, realism, silhouette, detail limits, background
    complexity, and forbidden styles.
  - Keep characters recognizable through broad features that survive temporal
    compression and resolution changes.
- [x] Complete `visual_style/lighting.yaml`.
  - Define stable indoor, outdoor, time-of-day, and weather families.
  - Preserve face readability and canonical material colors through changing light.
- [x] Complete `visual_style/materials.yaml`.
  - Define stable low-frequency surfaces for characters, props, and environments.
  - Include T2V, I2V, TI2V, and S2V-specific prompt and temporal-stability rules.
- [x] Create `visual_style/art-direction.yaml`.
  - Define focal hierarchy, subject-count limits, scale, visual density, movement
    space, landmark readability, decoration, signage, and environmental storytelling.
  - Define when the background must stay simple so it does not compete with the
    subject or create temporal warping.
  - Define framing margins for full-body action, hand–prop interaction, head turns,
    close facial performance, and slow camera movement.
  - Add reusable T2V scene-language, I2V preservation, TI2V simplification, and
    S2V face-readability fragments without writing shot-specific prompts.
- [x] Review `palette.yaml`, `palette-v2.yaml`, and `color_scripts.yaml`.
  - Choose one canonical palette and clearly deprecate or label alternatives.
  - Separate permanent local color from temporary lighting color.
  - Check that identity colors remain distinguishable at 480P and 720P and do not
    rely on tiny accents.
  - Remove or enlarge dense high-contrast patterns likely to shimmer or crawl.
- [x] Create `wan22-preproduction.yaml`.
  - Encode the four supported modes, their selection rules, required inputs,
    prohibited uses, draft-to-final escalation, and fallback decisions.
  - Define reusable prompt schemas for T2V and motion-only schemas for I2V.
  - Define S2V image-plus-audio readiness and identity invariants.
  - Record native model dimensions and frame-rate assumptions separately from
    delivery specifications, including TI2V's documented 720P/24 fps path.
  - Define neutral dry-run manifests that validate configuration without queuing
    generation or creating story content.

Completion check: an artist or image model can prepare one neutral, coherent
Wan-compatible reference frame using only approved visual-foundation files.

## Priority 2 — Finish reusable, generation-stable asset bibles

- [x] Create `assets/props.yaml`.
  - Give every recurring prop an ID, owner, purpose, dimensions, materials, colors,
    safe-use rules, sound identity, continuity states, and reference paths.
  - Define silhouette, orientation, hand-contact region, start state, end state,
    and allowed deformation for I2V motion.
  - Avoid tiny text, dense patterns, excessive moving parts, and ambiguous duplicates.
- [x] Create `assets/costumes.yaml`.
  - Keep shared costume policy in one catalogue and character-specific restrictions
    in the character files.
  - Use stable large color blocks and broad shapes; avoid fine stripes, tiny logos,
    jewelry-dependent identity, and motion-sensitive layered detail.
  - Define canonical, optional, seasonal, temporary-state, and forbidden items.
- [x] Create `assets/vehicles.yaml` for possible later additions.
  - Define scale, orientation, materials, seating, safe movement, character contact,
    sounds, and reference views.
  - Limit independent moving parts and specify one clear movement direction.
  - The registry is intentionally empty until a recurring vehicle is approved.
- [x] Create `assets/background-characters.yaml`.
  - Define allowed types, simplified materials, palette, behavior, crowd density,
    and silhouette separation from Riri and Yoyo.
  - Set conservative subject-count limits because extra characters and accidental
    faces can cause attention mixing and identity confusion.
- [x] Audit `locations-assets.yaml` and every location profile.
  - Separate permanent architecture and landmarks from movable props.
  - Add dimensions, entrances, exits, navigation areas, safe interaction zones,
    camera-safe views, movement space, and stable large-scale geometry.
  - Define a short T2V descriptor for exploratory environment views and approved
    I2V source frames for any exact recurring layout.
  - Simplify repeated background detail that can warp, flicker, or multiply.

Completion check: every recurring visible asset has a canonical ID, a readable
medium-scale identity, a valid reference strategy, and explicit motion states.

## Priority 3 — Finish Wan-compatible character performance foundations

- [x] Create `characters/animation-style.yaml`.
  - Define motion speed, weight, balance, squash-and-stretch, walk/run limits, idle
    behavior, gesture size, reaction timing, secondary motion, and unsafe motion.
  - Define a reusable one-action grammar: body part, direction, speed, range,
    repetition count, endpoint, locked regions, and camera behavior.
  - Prefer slow controlled movement for identity-critical I2V work and specify when
    complex action must be divided during production.
- [x] Create or consolidate `characters/acting-style.yaml`.
  - Define shared eye, face, head, body, listening, turn-taking, emotion intensity,
    gaze, silence, and expression-transition rules.
  - Add S2V rules for speech onset, pause-mouth rest, emphasized gestures, final
    mouth settle, and no speech-like movement during silence.
  - Define half-body and full-body performance limits while keeping eyes, mouth,
    Riri's muzzle, and Yoyo's beak readable.
- [x] Create `characters/relationships.yaml`.
  - Define cooperation, boundaries, reassurance, complementary learning roles,
    relative scale, screen-position preferences, eye lines, and safe contact.
  - Define clear two-character blocking so actions and props are not assigned to
    the wrong character.
- [x] Audit each `character.yaml`.
  - Confirm appearance, proportions, medium-sized identity features, expressions,
    poses, motion identity, wardrobe, forbidden changes, and reference paths.
  - Make source-image guidance mode-aware: T2V description, I2V identity invariants,
    TI2V draft simplification, and S2V facial-performance protection.
  - Remove duplicated non-character material from music profiles.
- [x] Create and approve character identity sheets.
  - Include front, side, back, three-quarter, expressions, poses, and scale comparison.
  - Use these for design review and identity checking, not directly as I2V or S2V
    inputs because collages and multi-view sheets can confuse generation.
  - Project-owner approval of the V1 Riri and Yoyo identity sheets and their shared
    scale comparison is recorded in `validation/project-owner-approvals.yaml`.
- [x] Create and approve single-frame generation references.
  - For I2V: action-compatible starting pose, visible contact points, correct
    anatomy, clear movement space, stable background, and delivery aspect ratio.
  - For S2V: separate neutral full-body and half-body frames with unobstructed eyes
    and mouth, clean facial boundaries, closed or resting mouth, and no text.
  - Register each frame by character, framing, pose, lighting, background, version,
    approved use, and forbidden use.
  - Project-owner approval of the four neutral V1 full-body and half-body frames is
    recorded in `validation/project-owner-approvals.yaml`.

Completion check: Riri and Yoyo remain recognizable and their reusable motion and
performance rules can be translated into I2V or S2V inputs without story context.

## Priority 4 — Finish brand, reference, and reproducibility governance

- [x] Create `brand.yaml`.
  - Define logo, typography, title treatment, icons, colors, clear space, prohibited
    treatments, and child-readable text.
  - Treat critical text and logos as authored overlay assets; do not rely on Wan
    generation to render readable typography inside video frames.
- [x] Create `references.yaml`.
  - Register character, single-frame generation, location, prop, lighting, material,
    and style references with status, version, source path, and replacement history.
  - Add `allowed_modes`, `authority`, `aspect_ratio`, `pixel_dimensions`,
    `framing`, `starting_pose`, `movement_space`, and `known_limitations`.
  - Distinguish design sheets from images approved as I2V or S2V conditioning input.
- [x] Create `asset-conventions.yaml`.
  - Define IDs, filenames, folders, versions, approval states, variants, and deprecation.
  - Define generation-record names containing task mode, prompt version, reference
    version, seed, dimensions, frame count, candidate number, and audio hash where used.
  - Never encode only a random numeric node ID as workflow meaning.
- [x] Define required location and asset reference views.
  - Locations: master view, reverse view, entrance, landmark, action area, lighting
    states, scale reference, and clean single-frame I2V views.
  - Props and vehicles: turnaround, dimensions, interaction view, orientation,
    canonical state, and simple state variants.
  - Confirm each generation source is one coherent frame, never a board or collage.
- [ ] Review and either promote or reject the Riri V2 visual package.
  - Review `characters/riri/character-v2.yaml` with its five registered V2 design sheets.
  - Keep V1 canonical and keep all V2 boards forbidden as conditioning inputs until
    the package is approved and clean V2 single-frame generation references exist.
  - Treat the lavender bow/collar on the close-up board as noncanonical exploration.
- [ ] Review and either promote or reject the Yoyo V2 visual package.
  - Review `characters/yoyo/character-v2.yaml` with its five registered V2 design sheets.
  - Keep V1 canonical and keep all V2 boards forbidden as conditioning inputs until
    the package is approved and clean V2 single-frame generation references exist.
- [ ] Complete and review the Kindergarten Interior V2 location package.
  - All five camelCase-named reference boards are registered in
    `locations/interiors/location-v2.yaml` with 60 panel-purpose mappings, hashes,
    dimensions, scale consensus, zones, materials, lighting, and MCP routing.
  - Review the complete package and explicitly approve or reject V2.
  - Keep V1 canonical and keep V2 boards forbidden as direct conditioning inputs.
- [ ] Recover, register, and review the Kindergarten Exterior V2 location package.
  - Reattach the eight unavailable `06_24_31 PM` and `06_25_02 PM` source boards.
  - Read each visible board title, rename each file canonically, and register its
    views, geometry, proportions, materials, lighting, continuity, and MCP routing.
  - Keep V1 canonical and forbid V2 boards as direct conditioning inputs.
- [ ] Recover, register, and review the Kindergarten Evening/Night V2 package.
  - Reattach the five unavailable `06_25_21 PM` and `06_25_22 PM` source boards.
  - Read each visible board title, rename each file canonically, and register its
    views, scale, night lighting, safety, continuity, and MCP retrieval context.
  - Keep V1 canonical and forbid V2 boards as direct conditioning inputs.
- [ ] Reconcile and review the Kindergarten Indoor Play Space V2 package.
  - Review the five title-renamed boards and `locations/play_spaces/location-v2.yaml`.
  - Select one consistent measurement table and wall-orientation layout; do not
    average the conflicting generated values.
  - Decide whether the board-B activity table and hanging lanterns are canonical.
  - Keep V1 canonical and keep all five boards forbidden as direct conditioning.
- [ ] Review the Countryside Golden-Hour V2 location package.
  - Review the five visible-title-renamed boards and the relative-unit site,
    terrain, landmark, material, vegetation, and lighting specification.
  - Confirm that the boards' “Nature Park” label remains an alias of the canonical
    `countryside-golden-hour` ID rather than merging with the daylight nature park.
  - Keep V1 canonical and keep all boards forbidden as direct conditioning.
- [ ] Reconcile and review the Nature Park V2 location package.
  - Review all five title-renamed boards and the 60-panel context inventory.
  - Select the intended medium-tree canopy width and large flower-group width,
    clarify the printed elevation-range meaning, and select primary shadow quality.
  - Keep V1 canonical and keep all boards forbidden as direct conditioning.
- [ ] Promote accepted V2 packages and create clean single-frame location references.
  - Run this only after each complete V2 package is explicitly approved or rejected
    and every recorded measurement, layout, taxonomy, and lighting conflict is closed.
  - For accepted location packages, create clean primary, reverse, landmark or
    entrance, action-area, scale, lighting, and mode-specific I2V frames.
  - Preserve V1 history, replacement links, filenames, dimensions, and hashes.

Completion check: every approved reference is discoverable, versioned, tied to one
canonical entity, and explicitly approved or forbidden for each Wan mode.

## Priority 5 — Complete S2V audio-input readiness

- [x] Create or consolidate `audios/s2v-input-spec.yaml`.
  - Define accepted formats, channels, sample rate, loudness, peak limit, noise floor,
    reverb limit, leading silence, trailing settle, and maximum reusable segment length.
  - Require clean speech without music, ambience, effects, clipping, denoising
    artifacts, or inconsistent timing.
  - Treat the approved audio hash as the performance timing lock.
- [x] Audit and approve Riri and Yoyo voice references for cloning suitability.
  - Confirm one speaker, stable identity, clear pronunciation, consistent apparent
    age, clean silence, and no background sound.
  - Keep voice-cloning reference audio separate from final locked dialogue inputs.
  - Technical evidence is recorded in `audios/voice-reference-audit.yaml`; the
    project-owner listening approval is recorded in
    `validation/project-owner-approvals.yaml`.
- [x] Define reusable S2V timing annotations.
  - Record silence, speech onset, pause, emphasized word, gesture opportunity,
    speech end, and final settle as time events.
  - Define safe chunk-boundary rules at sentence ends, long pauses, or stillness;
    forbid boundaries inside fast words, large gestures, or contact actions.
- [x] Define S2V review criteria.
  - Check lip onset, consonant closures, vowel openings, pauses, silent-mouth rest,
    gesture emphasis, final settle, identity, background, lighting, and framing.
  - Require separate ambience, effects, and music planning later in production;
    S2V speech input is not the complete soundtrack.

Completion check: a future locked dialogue asset and approved character frame can
be validated for S2V without inventing dialogue during pre-production.

## Priority 6 — Complete safety and Wan-aware validation

- [x] Create `safety.yaml`.
  - Define emotional intensity, common fears, imitation risks, physical hazards,
    sensory limits, forbidden imagery, and reassurance requirements.
  - Add generation-specific rejection rules for accidental extra limbs, merged
    characters, threatening object changes, unsafe contact, and distressing faces.
- [x] Create `educational-direction.yaml`.
  - Define learning philosophy, vocabulary level, participation style, repetition,
    caregiver expectations, and prohibited teaching patterns.
- [x] Create `preproduction-checklist.yaml`.
  - Verify required files, IDs, paths, references, inheritance, and canonical rules.
  - Add mode-specific gates for T2V descriptions, I2V source frames, TI2V draft
    policy, S2V image/audio pairs, and the Animate exclusion.
  - Verify reference anatomy, silhouette, subject count, aspect ratio, movement
    space, text removal, audio cleanliness, and reference approval.
- [x] Add automated YAML and asset validation.
  - Validate required fields, broken paths, duplicate IDs, unsupported modes, empty
    references, image dimensions, audio metadata, and missing hashes.
  - Validate dry-run manifests without downloading weights, enabling providers, or
    queueing generation.
- [x] Create reusable Wan 2.2 review cards.
  - Review in order: structure, composition, subject count, identity, motion,
    temporal stability, materials, fine detail, and audio alignment when applicable.
  - Classify failures as regenerate, adjust one variable, simplify prompt, replace
    source image or audio, switch supported mode, or redesign later production work.
- [x] Run and record the final cross-file consistency review.
  - The technical validator passes with no errors.
  - Strict approval validation remains blocked by V2 candidates, unavailable V2
    sources, and planned complete location-view sets, as required.
  - See `validation/final-consistency-review.yaml`; rerun strict validation after
    the human approval gates are resolved.

Completion check: pre-production passes all checks without relying on story, scene,
shot, dialogue, editing, export, or generated-video files.

## Pre-production exit gate

Do not begin story or production work until all of these are true:

- [x] The preschool series identity and the four-mode Wan 2.2 contract are approved.
- [x] Visual style, art direction, lighting, materials, and canonical palette are approved.
- [ ] Project owner confirms the complete Riri and Yoyo appearance, motion, acting,
  voice, and relationship scope.
- [x] I2V and S2V single-frame references pass anatomy, silhouette, framing,
  movement-space, and no-text/no-collage checks.
- [x] Core locations and recurring assets have canonical IDs and reference strategies.
- [x] S2V speech-input, timing-lock, and review rules are approved.
- [x] Audio, music, ambience, and sound-effect identities are approved.
- [ ] Project owner confirms the brand, naming, versioning, prompt, seed, reference,
  and hash governance scope.
- [x] Native-generation and final-delivery format policies are documented separately.
- [ ] Project owner confirms the safety and educational-direction scope.
- [ ] Strict approval validation passes with no candidate, planned, unavailable, or
  unresolved required references.
- [x] Wan Animate remains disabled unless a separate runtime-policy change is approved.
