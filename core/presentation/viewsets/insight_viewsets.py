from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.presentation.serializers.paper_serializers import (
    InsightSerializer,
)
from core.infrastructure.container import Container
from drf_yasg.utils import swagger_auto_schema

import logging

logger = logging.getLogger(__name__)


class InsightViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = []
    serializer_class = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.insight_service = Container.get_insight_service()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return []
        return []

    def get_serializer_class(self):
        action_serializer_map = {
            "get_research_insights": InsightSerializer,
        }
        return action_serializer_map.get(self.action, InsightSerializer)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(manual_parameters=[])
    def get_research_insights(self, request: Request) -> Response:
        try:
            return Response({"items": self.insight_service.get_research_insights()})

        except Exception as e:
            logger.error(f"Error in get research insights: {str(e)}")
            return Response(
                {"error": "Failed to perform get research insights"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(manual_parameters=[])
    def get_research_concepts(self, request: Request) -> Response:
        try:
            research_field = request.query_params.getlist("research_fields")
            return Response(self.insight_service.get_research_concepts(research_field))

        except Exception as e:
            logger.error(f"Error in get research concepts: {str(e)}")
            return Response(
                {"error": "Failed to perform get research concepts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(manual_parameters=[])
    def get_research_components(self, request: Request) -> Response:
        try:
            research_field = request.query_params.getlist("research_fields")
            return Response(
                self.insight_service.get_research_components(research_field)
            )

        except Exception as e:
            logger.error(f"Error in get research components: {str(e)}")
            return Response(
                {"error": "Failed to perform get research components"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
