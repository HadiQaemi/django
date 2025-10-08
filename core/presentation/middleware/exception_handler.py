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
    if isinstance(exc, DomainException):
        return handle_domain_exception(exc)

    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "status": "error",
            "code": response.status_code,
            "message": str(exc),
        }

        if isinstance(exc, ValidationError) and hasattr(exc, "detail"):
            error_data["validation_errors"] = exc.detail

        response.data = error_data
        return response

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
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_data = {
        "status": "error",
        "message": str(exc),
        "details": exc.details,
    }

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
        logger.error(f"{exc.__class__.__name__}: {str(exc)}")
        if hasattr(exc, "details") and exc.details:
            logger.error(f"Details: {exc.details}")

    error_data["code"] = status_code

    return JsonResponse(error_data, status=status_code)


class ExceptionHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response

        except Exception as exc:
            if isinstance(exc, DomainException):
                return handle_domain_exception(exc)

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
