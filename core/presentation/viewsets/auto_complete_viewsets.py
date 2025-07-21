from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.presentation.serializers.paper_serializers import (
    AutoCompleteSerializer,
)
from core.infrastructure.container import Container
from core.application.dtos.input_dtos import (
    AutoCompleteInputDTO,
)
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger(__name__)


class AutoCompleteViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = []
    serializer_class = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_complete_service = Container.get_auto_complete_service()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return []
        return []

    def get_serializer_class(self):
        action_serializer_map = {
            "get_authors_by_name": AutoCompleteSerializer,
            "get_academic_publishers_by_label": AutoCompleteSerializer,
            "get_research_fields_by_label": AutoCompleteSerializer,
            "get_keywords_by_label": AutoCompleteSerializer,
        }
        return action_serializer_map.get(self.action, AutoCompleteSerializer)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
        ]
    )
    def get_authors_by_name(self, request: Request) -> Response:
        self.pagination_class = None
        try:
            query = request.query_params.get("search", "")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = AutoCompleteInputDTO(
                query=query,
                page=page,
                page_size=page_size,
            )
            result = self.auto_complete_service.get_authors_by_name(search_dto)
            return Response({"items": result})

        except Exception as e:
            logger.error(f"Error in search authers by name: {str(e)}")
            return Response(
                {"error": "Failed to perform search authers by name"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
        ]
    )
    def get_academic_publishers_by_label(self, request: Request) -> Response:
        self.pagination_class = None
        try:
            query = request.query_params.get("search", "")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = AutoCompleteInputDTO(
                query=query,
                page=page,
                page_size=page_size,
            )
            result = self.auto_complete_service.get_academic_publishers_by_name(
                search_dto
            )
            return Response({"items": result})

        except Exception as e:
            logger.error(f"Error in search academic publishers by name: {str(e)}")
            return Response(
                {"error": "Failed to perform search academic publishers by name"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
        ]
    )
    def get_keywords_by_label(self, request: Request) -> Response:
        self.pagination_class = None
        try:
            query = request.query_params.get("search", "")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = AutoCompleteInputDTO(
                query=query,
                page=page,
                page_size=page_size,
            )
            result = self.auto_complete_service.get_keywords_by_label(search_dto)
            return Response({"items": result})

        except Exception as e:
            logger.error(f"Error in search keywords by label: {str(e)}")
            return Response(
                {"error": "Failed to perform search keywords"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
        ]
    )
    def get_research_fields_by_label(self, request: Request) -> Response:
        self.pagination_class = None
        try:
            query = request.query_params.get("search", "")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = AutoCompleteInputDTO(
                query=query,
                page=page,
                page_size=page_size,
            )
            result = self.auto_complete_service.get_research_fields_by_name(search_dto)
            return Response({"items": result})

        except Exception as e:
            logger.error(f"Error in search keywords by label: {str(e)}")
            return Response(
                {"error": "Failed to perform search keywords"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
