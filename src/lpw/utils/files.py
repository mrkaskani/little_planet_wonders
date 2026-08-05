"""Provide files services for the LPW cinematic pipeline."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from lpw.errors import (
    ContextNotFoundError,
    InvalidContextDataError,
)


def load_yaml(path: Path, *, required: bool = True) -> dict[str, Any]:
    """Load a YAML mapping, returning an empty mapping for optional files.

    Args:
        path (Path): Filesystem path read or written by the operation.
        required (bool): Whether absence of the requested file is an error. Defaults to
            ``True``.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        ContextNotFoundError: If inputs, context, state, or provider output are invalid.
        InvalidContextDataError: If inputs, context, state, or provider output are invalid.
    """

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
    """Load json.

    Args:
        path (Path): Filesystem path read or written by the operation.

    Returns:
        dict[str, Any]: Result produced by the operation.

    Raises:
        FileNotFoundError: If inputs, context, state, or provider output are invalid.
        ValueError: If inputs, context, state, or provider output are invalid.
    """
    if not path.is_file():
        raise FileNotFoundError(f"JSON file was not found: {path}")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return content


def atomic_write_yaml(path: Path, content: dict[str, Any]) -> None:
    """Atomically persist generated runtime state.

    Args:
        path (Path): Filesystem path read or written by the operation.
        content (dict[str, Any]): Structured content written to the destination.
    """

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


def atomic_write_json(path: Path, content: Any) -> None:
    """Atomically persist generated JSON metadata.

    Args:
        path (Path): Filesystem path read or written by the operation.
        content (Any): Structured content written to the destination.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                content,
                stream,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
