"""
Domain exceptions for the REBORN API.

These exceptions represent errors in the domain logic.
"""

from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base class for all domain exceptions."""

    default_message = "A domain error occurred"

    def __init__(
        self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFound(DomainException):
    """Exception raised when a requested entity is not found."""

    default_message = "Entity not found"

    def __init__(self, entity_type: str, entity_id: str, message: Optional[str] = None):
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(
            message or f"{entity_type} with ID {entity_id} not found", details
        )


class InvalidInput(DomainException):
    """Exception raised when input data is invalid."""

    default_message = "Invalid input data"


class AccessDenied(DomainException):
    """Exception raised when operation is not allowed."""

    default_message = "Access denied"


class SearchEngineError(DomainException):
    """Exception raised when there's an error with search engines."""

    default_message = "Search engine error"


class ScraperError(DomainException):
    """Exception raised when there's an error with the web scraper."""

    default_message = "Error while scraping data"


class ValidationError(DomainException):
    """Exception raised when validation fails."""

    default_message = "Validation error"


class DatabaseError(DomainException):
    """Exception raised when there's a database-related error."""

    default_message = "Database error"


class ExternalServiceError(DomainException):
    """Exception raised when an external service returns an error."""

    default_message = "External service error"

    def __init__(
        self,
        service_name: str,
        error_code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({"service": service_name, "error_code": error_code})
        super().__init__(
            message or f"Error from external service {service_name}: {error_code}",
            details,
        )


class RateLimitExceeded(DomainException):
    """Exception raised when a rate limit is exceeded."""

    default_message = "Rate limit exceeded"
