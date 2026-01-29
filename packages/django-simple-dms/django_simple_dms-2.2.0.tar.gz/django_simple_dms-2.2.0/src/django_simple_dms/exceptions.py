class ForbiddenException(Exception):
    pass


class ImporterError(RuntimeError):
    """Error raised when an error occurs while trying to import a set of documents."""


class UnmodifiableRecord(RuntimeError):
    """Record is immutable."""
