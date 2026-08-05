from __future__ import annotations

import re

from lpw.errors import InvalidContextIdentifierError


SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not SAFE_IDENTIFIER.fullmatch(value):
        raise InvalidContextIdentifierError(
            f"{field_name} may contain only letters, numbers, hyphens and underscores."
        )
    return value
