"""
Exception handling middleware for the REBORN API.

This module provides exception handling middleware and utility functions
for handling exceptions in the REST API.
"""

import logging
import traceback
from typing import Dict, Any, Optional

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError, NotFound

from core.domain.exceptions import (
    DomainException,
    EntityNotFound,
    InvalidInput,
    AccessDenied,
    SearchEngineError,
    ScraperError,
    ValidationError as DomainValidationError,
    DatabaseError,
    ExternalServiceError,
    RateLimitExceeded,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> JsonResponse:
    """
    Custom exception handler for REST framework.

    This handler formats exceptions in a consistent way and logs them appropriately.
    """
    # Handle domain exceptions
    if isinstance(exc, DomainException):
        return handle_domain_exception(exc)

    # Handle Django REST framework exceptions
    response = exception_handler(exc, context)

    if response is not None:
        # Format DRF exceptions in our standard format
        error_data = {
            "status": "error",
            "code": response.status_code,
            "message": str(exc),
        }

        if isinstance(exc, ValidationError) and hasattr(exc, "detail"):
            error_data["validation_errors"] = exc.detail

        response.data = error_data
        return response

    # Handle unexpected exceptions
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    return JsonResponse(
        {
            "status": "error",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "An unexpected error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def handle_domain_exception(exc: DomainException) -> JsonResponse:
    """Handle domain-specific exceptions."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_data = {
        "status": "error",
        "message": str(exc),
        "details": exc.details,
    }

    # Map domain exceptions to HTTP status codes
    if isinstance(exc, EntityNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (InvalidInput, DomainValidationError)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AccessDenied):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, RateLimitExceeded):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(
        exc, (SearchEngineError, ScraperError, DatabaseError, ExternalServiceError)
    ):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # Log these exceptions as they indicate system issues
        logger.error(f"{exc.__class__.__name__}: {str(exc)}")
        if hasattr(exc, "details") and exc.details:
            logger.error(f"Details: {exc.details}")

    error_data["code"] = status_code

    return JsonResponse(error_data, status=status_code)


class ExceptionHandlerMiddleware:
    """
    Middleware for handling exceptions globally.

    This middleware catches exceptions that might occur outside the DRF view context,
    such as in middleware or URL routing.
    """

    def __init__(self, get_response):
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request."""
        try:
            response = self.get_response(request)
            return response

        except Exception as exc:
            # Handle domain exceptions
            if isinstance(exc, DomainException):
                return handle_domain_exception(exc)

            # Handle unexpected exceptions
            logger.error(f"Unhandled exception in middleware: {exc}")
            logger.error(traceback.format_exc())

            return JsonResponse(
                {
                    "status": "error",
                    "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": "An unexpected error occurred.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
