"""Backward-compatible imports for the reorganized context package."""

from lpw.config import context_root
from lpw.context.compiler import ContextCompiler, ContextCompilerError
from lpw.context.loader import (
    get_project_directory,
    load_audio_context,
    load_character,
    load_location,
    load_project_context,
    load_voice,
)
from lpw.context.pipeline import SceneContextPipeline
from lpw.errors import (
    ContextError,
    ContextNotFoundError,
    InvalidContextDataError,
    InvalidContextIdentifierError,
)
from lpw.utils.files import load_yaml
from lpw.utils.hashing import stable_hash as calculate_context_hash
from lpw.utils.identifiers import validate_identifier
from lpw.utils.mappings import deep_merge

CONTEXT_ROOT = context_root()

__all__ = [
    "CONTEXT_ROOT",
    "ContextCompiler",
    "ContextCompilerError",
    "ContextError",
    "ContextNotFoundError",
    "InvalidContextDataError",
    "InvalidContextIdentifierError",
    "SceneContextPipeline",
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
