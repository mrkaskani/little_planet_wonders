"""Provide loader services for the LPW cinematic pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from lpw.config import context_root
from lpw.errors import ContextNotFoundError
from lpw.utils.files import load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier
from lpw.utils.mappings import deep_merge


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


def load_character(project_directory: Path, character_id: str) -> dict[str, Any]:
    """Load character.

    Args:
        project_directory (Path): Project directory used by this operation.
        character_id (str): Stable identifier of the character.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """
    character_id = validate_identifier(character_id, "character_id")
    return _load_first(
        [
            project_directory / "characters" / f"{character_id}.yaml",
            project_directory / "characters" / character_id / "character.yaml",
        ],
        required=True,
    )


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
        return direct
    locations_directory = project_directory / "locations"
    if locations_directory.is_dir():
        for path in sorted(locations_directory.glob("*/location.yaml")):
            candidate = load_yaml(path)
            if candidate.get("id") == location_id:
                return candidate
    raise ContextNotFoundError(f"Location does not exist: {location_id}")


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
) -> dict[str, Any]:
    """Load the project's flat or nested schema without modifying source files.

    Args:
        project_id (str): Stable identifier of the project whose context is used.
        character_ids (list[str] | None): Character identifiers whose context should be
            included. Defaults to ``None``.
        location_id (str | None): Stable identifier of the location. Defaults to
            ``None``.

    Returns:
        dict[str, Any]: Result produced by the operation.
    """

    project_directory = get_project_directory(project_id)
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
            for character_id in character_ids or []
        ],
        "location": load_location(project_directory, location_id) if location_id else None,
    }
    context["metadata"] = {
        "project_id": project_id,
        "character_ids": character_ids or [],
        "location_id": location_id,
    }
    context["metadata"]["context_hash"] = stable_hash(context)
    return context
