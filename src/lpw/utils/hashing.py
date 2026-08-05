"""Provide hashing services for the LPW cinematic pipeline."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(value: Any, *, length: int = 16) -> str:
    """Execute hash.

    Args:
        value (Any): Value inspected or transformed by the helper.
        length (int): Length used by this operation. Defaults to ``16``.

    Returns:
        str: Result produced by the operation.
    """
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]
