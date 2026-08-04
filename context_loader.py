"""Backward-compatible imports for the reorganized context package."""

from little_planet_wonders.config import context_root
from little_planet_wonders.context.loader import (
    get_project_directory,
    load_audio_context,
    load_character,
    load_location,
    load_project_context,
    load_voice,
)
from little_planet_wonders.errors import (
    ContextError,
    ContextNotFoundError,
    InvalidContextDataError,
    InvalidContextIdentifierError,
)
from little_planet_wonders.utils.files import load_yaml
from little_planet_wonders.utils.hashing import stable_hash as calculate_context_hash
from little_planet_wonders.utils.identifiers import validate_identifier
from little_planet_wonders.utils.mappings import deep_merge

CONTEXT_ROOT = context_root()

__all__ = [
    "CONTEXT_ROOT",
    "ContextError",
    "ContextNotFoundError",
    "InvalidContextDataError",
    "InvalidContextIdentifierError",
    "calculate_context_hash",
    "deep_merge",
    "get_project_directory",
    "load_audio_context",
    "load_character",
    "load_location",
    "load_project_context",
    "load_voice",
    "load_yaml",
    "validate_identifier",
]
