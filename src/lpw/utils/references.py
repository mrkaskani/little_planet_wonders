"""Provide references services for the LPW cinematic pipeline."""

from __future__ import annotations

from typing import Any


def collect_reference_images(value: Any) -> list[str]:
    """Recursively collect unique image references while preserving order.

    Args:
        value (Any): Value inspected or transformed by the helper.

    Returns:
        list[str]: Result produced by the operation.
    """

    references: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "reference_images":
                if isinstance(child, dict):
                    references.extend(str(path) for path in child.values())
                elif isinstance(child, list):
                    references.extend(str(path) for path in child)
            else:
                references.extend(collect_reference_images(child))
    elif isinstance(value, list):
        for child in value:
            references.extend(collect_reference_images(child))
    return list(dict.fromkeys(references))
