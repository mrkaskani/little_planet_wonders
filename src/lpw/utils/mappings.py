from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, override_value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(override_value, dict):
            result[key] = deep_merge(existing, override_value)
        else:
            result[key] = deepcopy(override_value)
    return result
