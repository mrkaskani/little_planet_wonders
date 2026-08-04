from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from little_planet_wonders.errors import (
    ContextNotFoundError,
    InvalidContextDataError,
)


def load_yaml(path: Path, *, required: bool = True) -> dict[str, Any]:
    """Load a YAML mapping, returning an empty mapping for optional files."""

    if not path.is_file():
        if required:
            raise ContextNotFoundError(f"Required context file was not found: {path}")
        return {}

    with path.open("r", encoding="utf-8") as stream:
        content = yaml.safe_load(stream)

    if content is None:
        return {}
    if not isinstance(content, dict):
        raise InvalidContextDataError(f"YAML root must be an object: {path}")
    return content


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"JSON file was not found: {path}")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return content


def atomic_write_yaml(path: Path, content: dict[str, Any]) -> None:
    """Atomically persist generated runtime state."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(content, stream, sort_keys=False, allow_unicode=True)
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
