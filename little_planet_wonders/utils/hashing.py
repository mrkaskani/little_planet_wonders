from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash(value: Any, *, length: int = 16) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]
