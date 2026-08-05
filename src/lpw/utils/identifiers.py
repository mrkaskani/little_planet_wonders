"""Provide identifiers services for the LPW cinematic pipeline."""

from __future__ import annotations

import re

from lpw.errors import InvalidContextIdentifierError


SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_identifier(value: str, field_name: str) -> str:
    """Validate identifier.

    Args:
        value (str): Value inspected or transformed by the helper.
        field_name (str): Field name used by this operation.

    Returns:
        str: Result produced by the operation.

    Raises:
        InvalidContextIdentifierError: If inputs, context, state, or provider output are invalid.
    """
    if not isinstance(value, str) or not SAFE_IDENTIFIER.fullmatch(value):
        raise InvalidContextIdentifierError(
            f"{field_name} may contain only letters, numbers, hyphens and underscores."
        )
    return value
