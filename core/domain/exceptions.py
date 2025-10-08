from typing import Optional, Dict, Any


class DomainException(Exception):
    default_message = "A domain error occurred"

    def __init__(
        self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class EntityNotFound(DomainException):
    default_message = "Entity not found"

    def __init__(self, entity_type: str, entity_id: str, message: Optional[str] = None):
        details = {"entity_type": entity_type, "entity_id": entity_id}
        super().__init__(
            message or f"{entity_type} with ID {entity_id} not found", details
        )


class InvalidInput(DomainException):
    default_message = "Invalid input data"


class AccessDenied(DomainException):
    default_message = "Access denied"


class SearchEngineError(DomainException):
    default_message = "Search engine error"


class ScraperError(DomainException):
    default_message = "Error while scraping data"


class ValidationError(DomainException):
    default_message = "Validation error"


class DatabaseError(DomainException):
    default_message = "Database error"


class ExternalServiceError(DomainException):
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
    default_message = "Rate limit exceeded"
