"""Define domain-specific exceptions raised by LPW services."""

class ContextError(Exception):
    """Base error for cinematic context problems."""


class ContextNotFoundError(ContextError):
    """Raised when required context is unavailable."""


class InvalidContextIdentifierError(ContextError):
    """Raised when an identifier could escape its expected directory."""


class InvalidContextDataError(ContextError):
    """Raised when a context document has an invalid root value."""
