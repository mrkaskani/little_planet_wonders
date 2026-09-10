"""Provide loader services for the LPW cinematic pipeline."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from lpw.config import context_root
from lpw.errors import ContextNotFoundError, InvalidContextDataError
from lpw.utils.files import load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier
from lpw.utils.mappings import deep_merge


EMOTION_CONTRACT_ALIASES = {
    "happy": "happiness",
    "curious": "curiosity",
    "surprised": "surprise",
    "worried": "worry_or_concern",
    "sad": "sadness",
}


def get_project_directory(project_id: str) -> Path:
    """Return project directory.

    Args:
        project_id (str): Stable identifier of the project whose context is used.

    Returns:
        Path: Result produced by the operation.

    Raises:
        ValueError: If inputs, context, state, or provider output are invalid.
        ContextNotFoundError: If inputs, context, state, or provider output are invalid.
    """
    project_id = validate_identifier(project_id, "project_id")
    projects_root = (context_root() / "projects").resolve()
    project_directory = (projects_root / project_id).resolve()
    if projects_root not in project_directory.parents:
        raise ValueError("Project path is outside the configured context root.")
    if not project_directory.is_dir():
        raise ContextNotFoundError(f"Project does not exist: {project_id}")
    return project_directory


def _load_first(paths: Iterable[Path], *, required: bool = False) -> dict[str, Any]:
    """Load first.

    Args:
        paths (Iterable[Path]): Paths used by this operation.
        required (bool): Whether absence of the requested file is an error. Defaults to
            ``False``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ContextNotFoundError: If inputs, context, state, or provider output are invalid.
    """
    candidates = list(paths)
    for path in candidates:
        if path.is_file():
            return load_yaml(path)
    if required:
        rendered = ", ".join(str(path) for path in candidates)
        raise ContextNotFoundError(f"None of the required context files exist: {rendered}")
    return {}


def _load_directory(directory: Path) -> dict[str, Any]:
    """Load directory.

    Args:
        directory (Path): Directory used by this operation.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    combined: dict[str, Any] = {}
    if directory.is_dir():
        for path in sorted(directory.glob("*.yaml")):
            combined = deep_merge(combined, load_yaml(path))
    return combined


def _is_approved_canonical_version(context: dict[str, Any]) -> bool:
    """Return whether a versioned visual context is approved and canonical.

    Args:
        context: Versioned character or location context to inspect.

    Returns:
        Whether the context status and active version mark it as canonical.
    """

    status = str(context.get("status", ""))
    versioning = context.get("versioning", {})
    if not isinstance(versioning, dict):
        versioning = {}
    version_tag = context.get("version_tag")
    active_version = versioning.get("active_canonical_version")
    return status.startswith("approved-canonical") and (
        version_tag is None or active_version == version_tag
    )


def _merge_canonical_visual_version(
    base: dict[str, Any],
    visual: dict[str, Any],
    *,
    entity_id: str,
    authority: str,
) -> dict[str, Any]:
    """Overlay approved visual authority while retaining base nonvisual context.

    Args:
        base: Existing entity context containing reusable nonvisual fields.
        visual: Approved versioned visual context overlaid on the base.
        entity_id: Stable canonical character or location identifier.
        authority: Project-relative path of the resolved visual authority.

    Returns:
        Combined canonical context with visual resolution metadata.
    """

    resolved = deep_merge(base, visual)
    resolved["id"] = entity_id
    metadata = resolved.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        resolved["metadata"] = metadata
    metadata["canonical_entity_id"] = entity_id
    metadata["resolved_visual_authority"] = authority
    metadata["resolved_visual_version"] = visual.get("version_tag", visual.get("version"))
    return resolved


def load_character(project_directory: Path, character_id: str) -> dict[str, Any]:
    """Load character.

    Args:
        project_directory (Path): Project directory used by this operation.
        character_id (str): Stable identifier of the character.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    character_id = validate_identifier(character_id, "character_id")
    base = _load_first(
        [
            project_directory / "characters" / f"{character_id}.yaml",
            project_directory / "characters" / character_id / "character.yaml",
        ],
        required=True,
    )
    visual_path = (
        project_directory / "characters" / character_id / "character-v2.yaml"
    )
    visual = load_yaml(visual_path, required=False)
    if visual and _is_approved_canonical_version(visual):
        return _merge_canonical_visual_version(
            base,
            visual,
            entity_id=character_id,
            authority=visual_path.relative_to(project_directory).as_posix(),
        )
    return base


def load_location(project_directory: Path, location_id: str) -> dict[str, Any]:
    """Load location.

    Args:
        project_directory (Path): Project directory used by this operation.
        location_id (str): Stable identifier of the location.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    location_id = validate_identifier(location_id, "location_id")
    direct = _load_first(
        [
            project_directory / "locations" / f"{location_id}.yaml",
            project_directory / "locations" / location_id / "location.yaml",
        ],
        required=False,
    )
    if direct:
        direct_path = project_directory / "locations" / location_id / "location.yaml"
        visual_path = direct_path.with_name("location-v2.yaml")
        visual = load_yaml(visual_path, required=False)
        if visual and _is_approved_canonical_version(visual):
            return _merge_canonical_visual_version(
                direct,
                visual,
                entity_id=location_id,
                authority=visual_path.relative_to(project_directory).as_posix(),
            )
        return direct
    locations_directory = project_directory / "locations"
    if locations_directory.is_dir():
        # Exact versioned IDs remain directly retrievable. When the canonical
        # location ID is requested, an approved canonical V2 sibling overlays
        # the base location so nonvisual policies remain available.
        for path in sorted(locations_directory.glob("*/location*.yaml")):
            candidate = load_yaml(path)
            if candidate.get("id") == location_id:
                if path.name == "location.yaml":
                    visual_path = path.with_name("location-v2.yaml")
                    visual = load_yaml(visual_path, required=False)
                    if visual and _is_approved_canonical_version(visual):
                        return _merge_canonical_visual_version(
                            candidate,
                            visual,
                            entity_id=location_id,
                            authority=visual_path.relative_to(project_directory).as_posix(),
                        )
                return candidate
    raise ContextNotFoundError(f"Location does not exist: {location_id}")


def load_episode(project_directory: Path, episode_id: str) -> dict[str, Any]:
    """Load a project episode by folder name or exact YAML identifier.

    Args:
        project_directory (Path): Project directory used by this operation.
        episode_id (str): Stable identifier of the episode.

    Returns:
        dict[str, Any]: Raw episode context from its YAML authority.

    Raises:
        ContextNotFoundError: If the episode cannot be found.
        InvalidContextDataError: If a directly addressed episode has a different ID.
    """

    episode_id = validate_identifier(episode_id, "episode_id")
    direct_paths = [
        project_directory / "episodes" / f"{episode_id}.yaml",
        project_directory / "episodes" / episode_id / "episode.yaml",
    ]
    for path in direct_paths:
        if path.is_file():
            episode = load_yaml(path)
            if episode.get("id") != episode_id:
                raise InvalidContextDataError(
                    f"Episode file '{path}' contains ID {episode.get('id')!r}, "
                    f"expected '{episode_id}'."
                )
            return episode

    episodes_directory = project_directory / "episodes"
    if episodes_directory.is_dir():
        for path in sorted(episodes_directory.glob("*/episode*.yaml")):
            candidate = load_yaml(path)
            if candidate.get("id") == episode_id:
                return candidate
    raise ContextNotFoundError(f"Episode does not exist: {episode_id}")


def _resolve_episode_character(
    project_directory: Path,
    state: dict[str, Any],
    acting_style: dict[str, Any],
) -> dict[str, Any]:
    """Resolve one episode character state against character and acting authorities.

    Args:
        project_directory: Project directory containing character authorities.
        state: Episode-local character, emotion, and performance selection.
        acting_style: Shared acting intensity and emotion-contract authority.

    Returns:
        Character context with resolved V2 visuals, emotion, and acting data.

    Raises:
        InvalidContextDataError: If the episode selects an unknown emotion or intensity.
    """

    character_id = validate_identifier(state.get("id"), "character_id")
    character = load_character(project_directory, character_id)
    raw_emotion = state.get("emotion", {"id": "neutral", "intensity": "level_1"})
    if isinstance(raw_emotion, str):
        raw_emotion = {"id": raw_emotion}
    if not isinstance(raw_emotion, dict):
        raise InvalidContextDataError(
            f"Episode character '{character_id}' emotion must be a string or object."
        )

    emotion_id = validate_identifier(raw_emotion.get("id"), "emotion_id")
    expression_library = character.get("expression_library", {})
    expression = expression_library.get(emotion_id)
    if not isinstance(expression, dict):
        available = ", ".join(sorted(expression_library)) or "none"
        raise InvalidContextDataError(
            f"Character '{character_id}' does not define emotion/expression "
            f"'{emotion_id}'. Available expressions: {available}."
        )

    intensity_id = validate_identifier(
        raw_emotion.get("intensity", "level_2"), "emotion_intensity"
    )
    intensity = acting_style.get("intensity_scale", {}).get(intensity_id)
    if not isinstance(intensity, dict):
        raise InvalidContextDataError(
            f"Episode character '{character_id}' uses unknown emotion intensity "
            f"'{intensity_id}'."
        )

    contract_id = raw_emotion.get("contract") or EMOTION_CONTRACT_ALIASES.get(
        emotion_id
    )
    contract = None
    if contract_id is not None:
        contract_id = validate_identifier(contract_id, "emotion_contract")
        contract = acting_style.get("emotion_contracts", {}).get(contract_id)
        if not isinstance(contract, dict):
            raise InvalidContextDataError(
                f"Episode character '{character_id}' uses unknown emotion contract "
                f"'{contract_id}'."
            )

    return {
        "id": character_id,
        "episode_state": deepcopy(state),
        "character": character,
        "resolved_emotion": {
            "id": emotion_id,
            "intensity": intensity_id,
            "expression": deepcopy(expression),
            "intensity_context": deepcopy(intensity),
            "contract_id": contract_id,
            "contract": deepcopy(contract),
        },
        "performance_signature": deepcopy(
            acting_style.get("character_performance_signatures", {}).get(
                character_id, {}
            )
        ),
    }


def load_episode_context(
    project_directory: Path, episode_id: str
) -> dict[str, Any]:
    """Load an episode and resolve its character emotions and default location.

    Args:
        project_directory (Path): Project directory used by this operation.
        episode_id (str): Stable identifier of the episode.

    Returns:
        dict[str, Any]: Episode context with full character and emotion authorities.

    Raises:
        InvalidContextDataError: If the episode character declarations are invalid.
    """

    episode = load_episode(project_directory, episode_id)
    character_states = episode.get("characters")
    if not isinstance(character_states, list) or not character_states:
        raise InvalidContextDataError(
            f"Episode '{episode_id}' requires a non-empty characters list."
        )
    if not all(isinstance(state, dict) for state in character_states):
        raise InvalidContextDataError(
            f"Episode '{episode_id}' characters must be YAML objects."
        )

    character_ids = [
        validate_identifier(state.get("id"), "character_id")
        for state in character_states
    ]
    if len(character_ids) != len(set(character_ids)):
        raise InvalidContextDataError(
            f"Episode '{episode_id}' contains duplicate character IDs."
        )

    acting_style = _load_first(
        [project_directory / "characters" / "acting-style.yaml"], required=True
    )
    location_id = episode.get("location_id")
    if location_id is not None:
        location_id = validate_identifier(location_id, "location_id")

    resolved: dict[str, Any] = {
        "episode": episode,
        "characters": [
            _resolve_episode_character(project_directory, state, acting_style)
            for state in character_states
        ],
        "acting_style": acting_style,
        "location": (
            load_location(project_directory, location_id) if location_id else None
        ),
        "metadata": {
            "episode_id": episode_id,
            "character_ids": character_ids,
            "location_id": location_id,
        },
    }
    resolved["metadata"]["context_hash"] = stable_hash(resolved)
    return resolved


def audio_directory(project_directory: Path) -> Path:
    """Execute directory.

    Args:
        project_directory (Path): Project directory used by this operation.

    Returns:
        Path: Result produced by the operation.
    """
    for name in ("audio", "audios"):
        candidate = project_directory / name
        if candidate.is_dir():
            return candidate
    return project_directory / "audio"


def load_audio_context(project_id: str) -> dict[str, Any]:
    """Load audio context.

    Args:
        project_id (str): Stable identifier of the project whose context is used.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    directory = audio_directory(get_project_directory(project_id))
    audio = _load_first([directory / "audio.yaml"], required=False)
    return {
        "audio": audio,
        "audio_style": _load_first(
            [directory / "audio-style.yaml", directory / "audio_style.yaml"],
            required=False,
        ),
        "music": _load_first([directory / "music.yaml"], required=False),
        "ambience": _load_first([directory / "ambience.yaml"], required=False),
        "sound_effects": _load_first(
            [directory / "sound-effects.yaml", directory / "sound_effects.yaml"],
            required=False,
        ),
        "mixing": _load_first([directory / "mixing.yaml"], required=False),
        "continuity": _load_first(
            [
                directory / "audio-continuity.yaml",
                directory / "audio_continuity.yaml",
            ],
            required=False,
        ),
        "pronunciation": _load_first(
            [directory / "pronunciation.yaml"], required=False
        ),
        "voice_production": _load_first(
            [directory / "voice-production.yaml"], required=False
        ),
        "s2v_input_spec": _load_first(
            [directory / "s2v-input-spec.yaml"], required=False
        ),
        "voice_reference_audit": _load_first(
            [directory / "voice-reference-audit.yaml"], required=False
        ),
    }


def load_voice(project_id: str, character_id: str) -> dict[str, Any]:
    """Load a character-local voice profile or its legacy audio profile.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        character_id (str): Stable identifier of the character.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    character_id = validate_identifier(character_id, "character_id")
    project_directory = get_project_directory(project_id)
    directory = audio_directory(project_directory)
    return _load_first(
        [
            project_directory
            / "characters"
            / character_id
            / "voice-profile.yaml",
            directory / "voices" / f"{character_id}.yaml",
        ],
        required=False,
    )


def load_project_context(
    project_id: str,
    *,
    character_ids: list[str] | None = None,
    location_id: str | None = None,
    episode_id: str | None = None,
) -> dict[str, Any]:
    """Load the project's flat or nested schema without modifying source files.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        character_ids (list[str] | None): Character identifiers whose context should be
            included. Defaults to ``None``.
        location_id (str | None): Stable identifier of the location. Defaults to
            ``None``.
        episode_id (str | None): Stable identifier of an episode whose characters,
            emotions, and default location should be resolved. Defaults to ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    project_directory = get_project_directory(project_id)
    episode = (
        load_episode_context(project_directory, episode_id) if episode_id else None
    )
    resolved_character_ids = character_ids
    if resolved_character_ids is None and episode:
        resolved_character_ids = episode["metadata"]["character_ids"]
    resolved_character_ids = resolved_character_ids or []

    resolved_location_id = location_id
    if resolved_location_id is None and episode:
        resolved_location_id = episode["metadata"]["location_id"]

    audio = load_audio_context(project_id)
    continuity = deep_merge(
        load_yaml(project_directory / "continuity.yaml", required=False),
        _load_directory(project_directory / "continuity"),
    )
    context: dict[str, Any] = {
        "studio": load_yaml(context_root() / "studio.yaml"),
        "project": load_yaml(project_directory / "project.yaml"),
        "visual_style": _load_first(
            [
                project_directory / "visual-style.yaml",
                project_directory / "visual_style" / "visual_style.yaml",
            ]
        ),
        "color_palette": _load_first(
            [
                project_directory / "palette-v2.yaml",
                project_directory / "palette.yaml",
                project_directory / "visual_style" / "palette-v2.yaml",
                project_directory / "visual_style" / "palette.yaml",
            ]
        ),
        "color_scripts": _load_first(
            [
                project_directory / "color-scripts.yaml",
                project_directory / "visual_style" / "color_scripts.yaml",
            ]
        ),
        "lighting": _load_first(
            [
                project_directory / "lighting.yaml",
                project_directory / "visual_style" / "lighting.yaml",
            ]
        ),
        "materials": _load_first(
            [
                project_directory / "materials.yaml",
                project_directory / "visual_style" / "materials.yaml",
            ]
        ),
        "art_direction": _load_first(
            [
                project_directory / "art-direction.yaml",
                project_directory / "visual_style" / "art-direction.yaml",
            ]
        ),
        "wan_2_2": _load_first([project_directory / "wan22-preproduction.yaml"]),
        "s2v_runtime_profiles": _load_first(
            [project_directory / "wan22-s2v-runtime-profiles.yaml"], required=False
        ),
        "reference_sequence_prompt": _load_first(
            [
                project_directory
                / "generation-records"
                / "prompts"
                / "twelve-second-reference-sequence--s2v--prompt-v002.yaml",
                project_directory
                / "generation-records"
                / "prompts"
                / "five-second-reference-sequence--s2v--prompt-v001.yaml"
            ],
            required=False,
        ),
        "s2v_start_reference_prompt": _load_first(
            [
                project_directory
                / "generation-records"
                / "prompts"
                / "single-start-reference--wan22-s2v--prompt-v003.yaml"
            ],
            required=False,
        ),
        "s2v_dialogue_audio_prompt": _load_first(
            [
                project_directory
                / "generation-records"
                / "prompts"
                / "s2v-dialogue-audio-preparation--prompt-v001.yaml"
            ],
            required=False,
        ),
        "brand": _load_first([project_directory / "brand.yaml"], required=False),
        "references": _load_first(
            [project_directory / "references.yaml"], required=False
        ),
        "reference_views": _load_first(
            [project_directory / "reference-views.yaml"], required=False
        ),
        "asset_conventions": _load_first(
            [project_directory / "asset-conventions.yaml"], required=False
        ),
        "safety": _load_first([project_directory / "safety.yaml"], required=False),
        "educational_direction": _load_first(
            [project_directory / "educational-direction.yaml"], required=False
        ),
        "preproduction_checklist": _load_first(
            [project_directory / "preproduction-checklist.yaml"], required=False
        ),
        "wan_review_cards": _load_first(
            [project_directory / "wan22-review-cards.yaml"], required=False
        ),
        "animation_style": _load_first(
            [project_directory / "characters" / "animation-style.yaml"],
            required=False,
        ),
        "acting_style": _load_first(
            [project_directory / "characters" / "acting-style.yaml"],
            required=False,
        ),
        "relationships": _load_first(
            [project_directory / "characters" / "relationships.yaml"],
            required=False,
        ),
        "camera_language": _load_first(
            [
                project_directory / "camera-language.yaml",
                project_directory / "camera.yaml",
                project_directory / "cinematography" / "camera-language.yaml",
            ]
        ),
        "editing_style": _load_first([project_directory / "editing_style.yaml"]),
        "audio_style": audio["audio_style"],
        "audio": audio["audio"],
        "audio_context": audio,
        "continuity": continuity,
        "prop_catalog": _load_first(
            [
                project_directory / "assets" / "props.yaml",
                project_directory / "props.yaml",
            ]
        ),
        "costume_catalog": _load_first(
            [
                project_directory / "assets" / "costumes.yaml",
                project_directory / "costumes.yaml",
            ]
        ),
        "vehicle_catalog": _load_first(
            [
                project_directory / "assets" / "vehicles.yaml",
                project_directory / "vehicles.yaml",
            ]
        ),
        "background_character_catalog": _load_first(
            [
                project_directory / "assets" / "background-characters.yaml",
                project_directory / "background-characters.yaml",
            ]
        ),
        "props": _load_directory(project_directory / "props"),
        "wardrobe": _load_directory(project_directory / "wardrobe"),
        "negative_prompt": _load_first([project_directory / "negative-prompt.yaml"]),
        "characters": [
            load_character(project_directory, character_id)
            for character_id in resolved_character_ids
        ],
        "location": (
            load_location(project_directory, resolved_location_id)
            if resolved_location_id
            else None
        ),
    }
    if episode:
        context["episode"] = episode
    context["metadata"] = {
        "project_id": project_id,
        "character_ids": resolved_character_ids,
        "location_id": resolved_location_id,
    }
    if episode_id:
        context["metadata"]["episode_id"] = episode_id
    context["metadata"]["context_hash"] = stable_hash(context)
    return context
