"""Provide config services for the LPW cinematic pipeline."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parent


def _configured_path(variable: str, default: Path) -> Path:
    """Execute path.

    Args:
        variable (str): Variable used by this operation.
        default (Path): Default used by this operation.

    Returns:
        Path: Result produced by the operation.
    """
    return Path(os.getenv(variable, str(default))).expanduser().resolve()


def context_root() -> Path:
    """Return the read-only source-of-truth context directory.

    Returns:
        Path: Result produced by the operation.
    """

    configured = os.getenv("CINEMATIC_CONTEXT_ROOT") or os.getenv(
        "CINEMA_CONTEXT_ROOT"
    )
    return Path(configured).expanduser().resolve() if configured else (
        PACKAGE_ROOT / "context"
    ).resolve()


def workflows_root() -> Path:
    """Execute root.

    Returns:
        Path: Result produced by the operation.
    """
    return _configured_path("CINEMATIC_WORKFLOWS_ROOT", PROJECT_ROOT / "workflows")


def renders_root() -> Path:
    """Execute root.

    Returns:
        Path: Result produced by the operation.
    """
    return _configured_path("CINEMATIC_RENDER_ROOT", PROJECT_ROOT / "renders")


def runtime_root() -> Path:
    """Return the writable runtime directory, outside the packaged context.

    Returns:
        Path: Result produced by the operation.
    """

    return _configured_path("CINEMATIC_RUNTIME_ROOT", PROJECT_ROOT / "runtime")
