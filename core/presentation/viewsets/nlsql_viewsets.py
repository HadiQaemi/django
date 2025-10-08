from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from core.infrastructure.models.sql_models import DataItem
from core.infrastructure.services.nlsql_client import NLSQLClientService

logger = logging.getLogger(__name__)


class NLSQLViewSet(ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nlsql_service = NLSQLClientService()

    @swagger_auto_schema(
        operation_description="Check NL-SQL service health",
        responses={
            200: openapi.Response("Service is healthy"),
            503: openapi.Response("Service is unhealthy"),
        },
    )
    @action(detail=False, methods=["get"], url_path="health")
    def health_check(self, request):
        try:
            health_status = self.nlsql_service.health_check()

            if health_status.get("status") == "healthy":
                return Response(health_status, status=status.HTTP_200_OK)
            else:
                return Response(
                    health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return Response(
                {"status": "error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Get NL-SQL service status",
        responses={
            200: openapi.Response("Service status information"),
            500: openapi.Response("Error getting status"),
        },
    )
    @action(detail=False, methods=["get"], url_path="status")
    def service_status(self, request):
        try:
            service_status = self.nlsql_service.get_service_status()
            return Response(service_status, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return Response(
                {"status": "error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Generate SQL from natural language question",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["question"],
            properties={
                "question": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Natural language question"
                ),
                "schema": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Optional database schema context",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                "SQL generated successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "sql": openapi.Schema(type=openapi.TYPE_STRING),
                        "question": openapi.Schema(type=openapi.TYPE_STRING),
                        "confidence": openapi.Schema(type=openapi.TYPE_NUMBER),
                        # "similar_examples": openapi.Schema(
                        #     type=openapi.TYPE_ARRAY,
                        #     items=openapi.Items(type=openapi.TYPE_STRING),
                        #     description="Author IDs",
                        # ),
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response("Bad request"),
            500: openapi.Response("Internal server error"),
        },
    )
    @action(detail=False, methods=["post"], url_path="generate-sql")
    def generate_sql(self, request):
        try:
            question = request.data.get("question", "").strip()
            schema = request.data.get("schema")

            if not question:
                return Response(
                    {"error": "Question is required and cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = self.nlsql_service.generate_sql(question, schema)

            response_data = {
                "success": result.success,
                "sql": result.sql,
                "question": result.question,
                "confidence": result.confidence,
                "similar_examples": result.similar_examples or [],
                "error": result.error,
            }

            if result.success:
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"SQL generation error: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": f"Internal server error: {str(e)}",
                    "question": request.data.get("question", ""),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Generate SQL and execute it on CSV data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["question"],
            properties={
                "question": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Natural language question about the data",
                ),
                "data_item_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Optional: ID of specific DataItem to query (uses first if not provided)",
                ),
                "table_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Optional: Name for the table in DuckDB",
                    default="",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                "SQL executed successfully on data",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description="Query results",
                        ),
                        "columns": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            description="Column names",
                        ),
                        "row_count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "sql": openapi.Schema(type=openapi.TYPE_STRING),
                        "question": openapi.Schema(type=openapi.TYPE_STRING),
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response("Bad request"),
            500: openapi.Response("Internal server error"),
        },
    )
    @action(detail=False, methods=["post"], url_path="query-data")
    def query_data(self, request):
        try:
            question = request.data.get("question", "").strip()
            data_item_id = request.data.get("source")

            if not data_item_id:
                return Response(
                    {"error": "Source is required and cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = self.nlsql_service.generate_and_execute_sql(
                question=question,
                data_item_id=data_item_id,
                table_name=f"t{data_item_id}",
            )

            response_data = {
                "success": result.success,
                "data": result.data,
                "columns": result.columns,
                "row_count": result.row_count,
                "sql": result.sql,
                "question": result.question,
                "error": result.error,
            }

            if result.success:
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Query data error: {str(e)}")
            return Response(
                {
                    "success": False,
                    "error": f"Internal server error: {str(e)}",
                    "question": request.data.get("question", ""),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
