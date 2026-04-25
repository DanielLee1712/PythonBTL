class DomainException(Exception):
    """Base exception for domain errors."""
    pass


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found."""
    pass


class ValidationException(DomainException):
    """Raised when validation fails."""
    pass


class DuplicateEntityException(DomainException):
    """Raised when trying to create a duplicate entity."""
    pass
