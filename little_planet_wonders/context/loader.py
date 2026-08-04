from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from little_planet_wonders.config import context_root
from little_planet_wonders.errors import ContextNotFoundError
from little_planet_wonders.utils.files import load_yaml
from little_planet_wonders.utils.hashing import stable_hash
from little_planet_wonders.utils.identifiers import validate_identifier
from little_planet_wonders.utils.mappings import deep_merge


def get_project_directory(project_id: str) -> Path:
    project_id = validate_identifier(project_id, "project_id")
    projects_root = (context_root() / "projects").resolve()
    project_directory = (projects_root / project_id).resolve()
    if projects_root not in project_directory.parents:
        raise ValueError("Project path is outside the configured context root.")
    if not project_directory.is_dir():
        raise ContextNotFoundError(f"Project does not exist: {project_id}")
    return project_directory


def _load_first(paths: Iterable[Path], *, required: bool = False) -> dict[str, Any]:
    candidates = list(paths)
    for path in candidates:
        if path.is_file():
            return load_yaml(path)
    if required:
        rendered = ", ".join(str(path) for path in candidates)
        raise ContextNotFoundError(f"None of the required context files exist: {rendered}")
    return {}


def _load_directory(directory: Path) -> dict[str, Any]:
    combined: dict[str, Any] = {}
    if directory.is_dir():
        for path in sorted(directory.glob("*.yaml")):
            combined = deep_merge(combined, load_yaml(path))
    return combined


def load_character(project_directory: Path, character_id: str) -> dict[str, Any]:
    character_id = validate_identifier(character_id, "character_id")
    return _load_first(
        [
            project_directory / "characters" / f"{character_id}.yaml",
            project_directory / "characters" / character_id / "character.yaml",
        ],
        required=True,
    )


def load_location(project_directory: Path, location_id: str) -> dict[str, Any]:
    location_id = validate_identifier(location_id, "location_id")
    return _load_first(
        [
            project_directory / "locations" / f"{location_id}.yaml",
            project_directory / "locations" / location_id / "location.yaml",
        ],
        required=True,
    )


def audio_directory(project_directory: Path) -> Path:
    for name in ("audio", "audios"):
        candidate = project_directory / name
        if candidate.is_dir():
            return candidate
    return project_directory / "audio"


def load_audio_context(project_id: str) -> dict[str, Any]:
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
        "pronunciation": _load_first(
            [directory / "pronunciation.yaml"], required=False
        ),
    }


def load_voice(project_id: str, character_id: str) -> dict[str, Any]:
    character_id = validate_identifier(character_id, "character_id")
    directory = audio_directory(get_project_directory(project_id))
    return _load_first([directory / "voices" / f"{character_id}.yaml"], required=False)


def load_project_context(
    project_id: str,
    *,
    character_ids: list[str] | None = None,
    location_id: str | None = None,
) -> dict[str, Any]:
    """Load the project's flat or nested schema without modifying source files."""

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
                project_directory / "color-palette.yaml",
                project_directory / "palette.yaml",
                project_directory / "visual_style" / "palette.yaml",
            ]
        ),
        "lighting": _load_first(
            [
                project_directory / "lighting.yaml",
                project_directory / "visual_style" / "lighting.yaml",
            ]
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
        "continuity": continuity,
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
