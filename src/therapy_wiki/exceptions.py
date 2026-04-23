"""Typed exceptions for the workflow."""


class TherapyWikiError(RuntimeError):
    """Base project error."""


class MissingDependencyError(TherapyWikiError):
    """Raised when an external binary or Python package is missing."""


class SessionNotFoundError(TherapyWikiError):
    """Raised when a requested session does not exist."""


class DuplicateSourceError(TherapyWikiError):
    """Raised when an audio file was already ingested."""

