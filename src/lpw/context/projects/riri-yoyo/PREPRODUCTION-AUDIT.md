# Riri & Yoyo Pre-production Consistency Audit

Status: YAML structure and cross-file identity passed; asset-readiness gates remain open.

## Canonical contract

- Project ID: `riri-yoyo`
- Title: `Riri & Yoyo`
- Format: preschool episodic animation
- Audience: children ages 3–6
- Medium: stylized 3D animation
- Main characters: Riri and Yoyo
- Tone: warm, cheerful, gentle, playful, curious, comforting, emotionally clear, and child-safe
- Delivery foundation: 16:9, 1920×1080, 24 fps
- Canonical palette source: `visual_style/palette-v2.yaml`

## Normalizations completed

- Renamed the project context directory from `classroom` to `riri-yoyo`.
- Updated project IDs and project paths to `riri-yoyo`.
- Renamed `locations/interios` to `locations/interiors`.
- Renamed `locations/exterios` to `locations/exteriors`.
- Corrected `kindergarden` to `kindergarten` in IDs, prose, and references.
- Repaired location, music, sound, and palette YAML references.
- Added one approved Wan 2.2 pre-production contract for T2V, I2V, TI2V, and S2V.
- Kept Wan Animate disabled while preserving optional pose guidance as an S2V input.
- Separated native Wan generation formats from the 1920×1080, 24 fps delivery target.
- Selected `visual_style/palette-v2.yaml` as the canonical palette and deprecated `palette.yaml`.
- Replaced legacy thriller color-script states with reusable child-safe Riri and Yoyo states.
- Rebuilt the six visual `location.yaml` files instead of duplicating their sound profiles.
- Added task-specific Wan interfaces to visual style, art direction, lighting, materials, cinematography,
  character, location, and dialogue authorities.
- Removed duplicated character-bible content from both character music profiles.
- Aligned the dialogue-language contract to the approved English pronunciation and voice files.
- Added `audios/s2v-input-spec.yaml` and separated 24 kHz/16-bit voice-cloning references
  from future 48 kHz/24-bit mono locked S2V performance audio.
- Updated the context loader to prefer the canonical palette and expose the Wan, materials,
  color-script, art-direction, and S2V contracts.
- Added an approved reusable prop schema with an explicitly empty registry, preventing
  unapproved story props or placeholder references from becoming Wan inputs.
- Added an approved reusable costume schema, recorded both characters' no-clothing
  baselines, and kept the registry empty until a costume and character use are approved.
- Added an approved reusable vehicle schema for possible later additions, with no
  current vehicles and an empty registry that prevents unapproved vehicle invention.
- Preserved legitimate uses of `classroom` that describe the physical classroom location.
- Preserved horror, threat, and photorealism terms when they are explicit forbidden or negative-prompt constraints.

## Confirmed consistent

- Audience declarations use ages 3–6.
- Riri and Yoyo remain the only canonical main characters.
- Positive visual direction is stylized animation rather than photorealism or live action.
- Positive tone is gentle and child-safe.
- Character perceived ages are character-design attributes, not conflicting audience declarations.

## Deliberately deferred to later TODO items

These files are empty foundations rather than identity conflicts:

- `continuity.yaml`
- `continuity/location-states.yaml`

The location-state work remains tracked in `PREPRODUCTION-TODO.md`.

## Open pre-production gates

- Riri and Yoyo do not yet have approved single-frame visual references for I2V or S2V.
- All six locations still need approved visual reference views before exact geometry can be locked.
- Voice-reference file metadata passed, but audible cleanliness and speaker-consistency review
  still require listening QC before the voice-reference audit can be closed.
- The background-character catalogue, reference governance, animation/acting/relationship
  foundations, safety, education, and automated validation remain TODO.

## Files intentionally not Wan-refactored

Editing, take selection, color grade, subtitles, post-editing, and export YAMLs are
production or delivery concerns. Music, ambience, sound-effect, and location audio
profiles remain separate soundtrack authorities and must never be passed as S2V
conditioning audio. Their existing domain rules were left intact.
