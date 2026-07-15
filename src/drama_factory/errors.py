"""Domain errors with user-actionable context."""

class DramaFactoryError(Exception):
    """Base domain error."""


class ProjectNotFoundError(DramaFactoryError):
    """No project manifest could be discovered."""


class UnsupportedSchemaVersionError(DramaFactoryError):
    """Metadata declares an unsupported schema version."""


class InvalidMetadataError(DramaFactoryError):
    """Metadata does not meet an entity contract."""


class DuplicateEntityError(DramaFactoryError):
    """An entity ID appears more than once."""


class UnsafePathError(DramaFactoryError):
    """A metadata path is absolute, escaping, or otherwise unsafe."""


class MissingReferenceError(DramaFactoryError):
    """Metadata references an entity that was not indexed."""


class InvalidStateError(DramaFactoryError):
    """An entity state or relationship is not allowed."""


class ChecksumMismatchError(DramaFactoryError):
    """A referenced file does not match its declared checksum."""
