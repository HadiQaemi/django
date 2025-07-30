from core.presentation.permissions import (
    CanViewPapers,
    CanEditPapers,
    CanCreatePapers,
    CanDeletePapers,
    IsAdmin,
    IsEditor,
    IsViewer,
)
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from core.infrastructure.container import Container
from core.application.dtos.input_dtos import (
    QueryFilterInputDTO,
    ScraperUrlInputDTO,
)
from core.presentation.serializers.paper_serializers import (
    ArticleStatementsSerializer,
    ArticleWrapperSerializer,
    JournalSerializer,
    PaperListSerializer,
    PaperSerializer,
    AuthorSerializer,
    ConceptSerializer,
    ResearchFieldSerializer,
    StatementSerializer,
    PaperFilterSerializer,
    ScraperFlagSerializer,
    ScraperUrlSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class PaperViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = []
    serializer_class = PaperSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.paper_service = Container.get_paper_service()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return []
        return []

    def get_serializer_class(self):
        action_serializer_map = {
            "advanced_search": PaperFilterSerializer,
            "add_article_with_url": ScraperUrlSerializer,
            "add_all_papers": ScraperFlagSerializer,
            "get_authors": AuthorSerializer,
            "get_journals": JournalSerializer,
            "get_concepts": ConceptSerializer,
            "get_statements": StatementSerializer,
            "get_article_by_id": ArticleWrapperSerializer,
            "get_article_statements": ArticleStatementsSerializer,
            "get_articles": PaperListSerializer,
            "get_research_fields": ResearchFieldSerializer,
        }

        return action_serializer_map.get(self.action, PaperSerializer)

    # def get_permissions(self):
    #     if self.action in [
    #         "get_articles",
    #         "get_authors",
    #         "get_concepts",
    #         "get_statements",
    #         "get_article_by_id",
    #     ]:
    #         # permission_classes = [CanViewPapers]
    #         permission_classes = [AllowAny]
    #     elif self.action in ["add_article_with_url", "add_all_papers"]:
    #         permission_classes = [IsAuthenticated, CanCreatePapers]
    #     elif self.action in ["update_article"]:
    #         permission_classes = [IsAuthenticated, CanEditPapers]
    #     elif self.action in ["delete_article"]:
    #         permission_classes = [IsAuthenticated, CanDeletePapers]
    #     else:
    #         permission_classes = [IsAuthenticated]
    #     return [permission() for permission in permission_classes]

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "title",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Paper title",
            ),
            openapi.Parameter(
                "start_year",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Start year",
            ),
            openapi.Parameter(
                "end_year",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="End year",
            ),
            openapi.Parameter(
                "authors",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Author IDs",
            ),
            openapi.Parameter(
                "scientific_venues",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Scientific venue IDs",
            ),
            openapi.Parameter(
                "concepts",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Concept IDs",
            ),
            openapi.Parameter(
                "research_fields",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Research field IDs",
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Page number",
                default=1,
            ),
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Page size",
                default=10,
            ),
        ]
    )
    def advanced_search(self, request: Request) -> Response:
        """Query data with filters."""
        print("------------query_data---------1--")
        # try:
        # serializer = PaperFilterSerializer(data=request.data)
        # print("------------query_data---------2--")
        # if not serializer.is_valid():
        #     return Response(
        #         {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        #     )
        # print("------------query_data---------3--")
        author_param = request.query_params.get("authors", "")
        scientific_venue = request.query_params.get("scientific_venues", "")
        concept = request.query_params.get("concepts", "")
        research_field = request.query_params.get("research_fields", "")
        filter_dto = QueryFilterInputDTO(
            title=request.query_params.get("title"),
            start_year=request.query_params.get("time_range", {}).get("start"),
            end_year=request.query_params.get("time_range", {}).get("end"),
            author_ids=author_param.split(",") if author_param else [],
            scientific_venue_ids=scientific_venue.split(",")
            if scientific_venue
            else [],
            concept_ids=concept.split(",") if concept else [],
            research_field_ids=research_field.split(",") if research_field else [],
            page=request.query_params.get("page", 1),
            per_page=request.query_params.get("per_page", 10),
        )
        result = self.paper_service.query_data(filter_dto)
        return result

        # except Exception as e:
        #     logger.error(f"Error in query_data: {str(e)}")
        #     return Response(
        #         {"error": "Failed to query data"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

    @action(detail=False, methods=["get"])
    # @method_decorator(cache_page(60 * 15))
    # @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="ID of article",
            ),
        ]
    )
    def get_article_by_id(self, request: Request) -> Response:
        """Get latest articles with filters."""
        print("----get_article--------")
        self.pagination_class = None
        try:
            paper_id = request.query_params.get("id")
            result = self.paper_service.get_paper_by_id(paper_id)

            if not result.success:
                return Response(
                    {"error": result.message or "Paper not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(result.result)

        except Exception as e:
            logger.error(f"Error in get_articles: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest articles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # @action(detail=True, methods=["get"], url_path="statement")
    # @method_decorator(cache_page(60 * 15))
    # @method_decorator(vary_on_cookie)
    # def get_statement(self, request: Request, pk=None) -> Response:
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="ID of article",
            ),
        ]
    )
    def get_statement_by_id(self, request: Request) -> Response:
        """Get a statement by ID."""
        print("--------------get_statement-----------------", __file__)
        try:
            statement_id = request.query_params.get("id")
            if not statement_id:
                return Response(
                    {"error": "ID parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = self.paper_service.get_statement(statement_id)
            if not result.success:
                return Response(
                    {"error": result.message or "Statement not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result.result)

        except Exception as e:
            logger.error(f"Error in get_statement: {str(e)}")
            return Response(
                {"error": "Failed to retrieve statement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # @action(detail=True, methods=["get"], url_path="statement")
    # @method_decorator(cache_page(60 * 15))
    # @method_decorator(vary_on_cookie)
    # def get_statement(self, request: Request, pk=None) -> Response:
    @action(detail=False, methods=["get"])
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "id",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="ID of article",
            ),
        ]
    )
    def get_article_statements(self, request: Request) -> Response:
        """Get a statement by ID."""
        print("--------------get_article_statements-----------------", __file__)
        try:
            statement_id = request.query_params.get("id")
            if not statement_id:
                return Response(
                    {"error": "ID parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # result = self.paper_service.get_statement(statement_id)
            result = self.paper_service.get_article_statement(statement_id)
            if not result.success:
                return Response(
                    {"error": result.message or "Statement not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(result.result)

        except Exception as e:
            logger.error(f"Error in get_statement: {str(e)}")
            return Response(
                {"error": "Failed to retrieve statement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "name",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Name of Concepts",
            ),
        ]
    )
    def get_concepts(self, request: Request) -> Response:
        """Get concepts by name."""
        try:
            name = request.query_params.get("name", "")
            if not name:
                return Response([])

            concepts = self.paper_service.get_concepts(name)

            return Response(
                [{"id": concept.id, "name": concept.label} for concept in concepts]
            )

        except Exception as e:
            logger.error(f"Error in get_concepts: {str(e)}")
            return Response(
                {"error": "Failed to retrieve concepts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "label",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Label of research fields",
            ),
        ]
    )
    def get_research_fields(self, request: Request) -> Response:
        """Get research fields by label."""
        try:
            label = request.query_params.get("label", "")

            # Empty string returns all research fields
            research_fields = self.paper_service.get_research_fields(label)

            return Response(research_fields)

        except Exception as e:
            logger.error(f"Error in get_research_fields: {str(e)}")
            return Response(
                {"error": "Failed to retrieve research fields"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Number of page",
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Size of page",
            ),
            openapi.Parameter(
                "sort",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="a-z",
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
            openapi.Parameter(
                "research_fields",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Research field IDs",
            ),
        ]
    )
    def get_statements(self, request: Request) -> Response:
        """Get latest statements with filters."""
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")
            search_type = request.query_params.get("search_type", "keyword")

            if search_type not in ["keyword", "semantic", "hybrid"]:
                search_type = "keyword"

            result = self.paper_service.get_latest_statements(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
                search_type=search_type,
            )

            items = []
            print("--------------get_statements-----------", __file__)
            for statement in result.content:
                author_name = ""
                if hasattr(statement, "authors") and statement.authors:
                    author_name = statement.authors[0].label
                items.append(
                    {
                        "statement_id": statement.statement_id,
                        "name": statement.label,
                        "author": author_name,
                        "scientific_venue": statement.journal_conference,
                        "article": statement.article_name,
                        "date_published": statement.date_published.year
                        if statement.date_published
                        else None,
                        "search_type_used": search_type,
                    }
                )

            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_statements: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest statements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    # @method_decorator(cache_page(60 * 15))
    # @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Number of page",
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Size of page",
            ),
            openapi.Parameter(
                "sort",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="a-z",
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
            openapi.Parameter(
                "research_fields",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Research field IDs",
            ),
        ]
    )
    def get_articles(self, request: Request) -> Response:
        """Get latest articles with filters."""
        print("----get_articles-----------research_fields")
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")
            search_type = request.query_params.get("search_type", "keyword")

            if search_type not in ["keyword", "semantic", "hybrid"]:
                search_type = "keyword"
            print("--------search_type----------")
            print(search_type)
            result = self.paper_service.get_latest_articles(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
                search_type=search_type,
            )

            items = []
            for article in result.content:
                author_name = ""
                if hasattr(article, "authors") and article.authors:
                    author_name = article.authors[0].family_name
                items.append(
                    {
                        "article_id": article.article_id,
                        "name": article.name,
                        "author": author_name,
                        "scientific_venue": article.journal,
                        "date_published": article.date_published.year
                        if article.date_published
                        else None,
                        "search_type_used": search_type,
                    }
                )
            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_articles: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest articles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Number of page",
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Size of page",
            ),
            openapi.Parameter(
                "sort",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="a-z",
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
            openapi.Parameter(
                "research_fields",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Research field IDs",
            ),
        ]
    )
    def get_authors(self, request: Request) -> Response:
        """Get latest authors with filters."""
        print("-------------get_authors----------", __file__)
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")

            result = self.paper_service.get_latest_authors(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            items = [
                {
                    "orcid": author.orcid,
                    "author_id": author.author_id,
                    "name": author.label,
                }
                for author in result.content
            ]

            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_latest_authors: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest authors"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    # def get_latest_journals(self, request: Request) -> Response:
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Number of page",
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Size of page",
            ),
            openapi.Parameter(
                "sort",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="a-z",
            ),
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="search query",
            ),
            openapi.Parameter(
                "research_fields",
                openapi.IN_QUERY,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="Research field IDs",
            ),
        ]
    )
    def get_journals(self, request: Request) -> Response:
        """Get latest journals with filters."""
        print("-------------get_latest_journals----------", __file__)
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")

            result = self.paper_service.get_latest_journals(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
            return Response({"items": result.content, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest journals"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def add_article_with_url(self, request: Request) -> Response:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        if not (ip == "127.0.0.1" or ip == "10.114.149.127"):
            return Response(
                {"error": f"Forbidden from {ip}"},
                status=status.HTTP_403_FORBIDDEN,
            )
        # try:
        serializer = ScraperUrlSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url_dto = ScraperUrlInputDTO(url=serializer.validated_data["url"])
        result = self.paper_service.extract_paper(url_dto)

        if not result.success:
            return Response(
                {"error": result.message or "Failed to extract paper"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"result": True})

        # except Exception as e:
        #     logger.error(f"Error in add_paper: {str(e)}")
        #     return Response(
        #         {"error": "Failed to add paper"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

    @action(detail=False, methods=["post"])
    def add_all_papers(self, request: Request) -> Response:
        """Add multiple papers from predefined URLs."""
        try:
            success_count = 0
            failure_count = 0
            error_messages = []

            URLs = [
                "https://service.tib.eu/ldmservice/dataset/haris-2025-1",
                "https://service.tib.eu/ldmservice/dataset/babaei-giglou-2023-1",
                "https://service.tib.eu/ldmservice/dataset/millan-marquez-2024-1",
                "https://service.tib.eu/ldmservice/dataset/gentsch-2023-2",
                "https://service.tib.eu/ldmservice/dataset/baimuratov-2024-2",
                "https://service.tib.eu/ldmservice/dataset/perez-alvarez-2018-2",
                "https://service.tib.eu/ldmservice/dataset/pina-ortiz-2023-1",
                "https://service.tib.eu/ldmservice/dataset/akter-2023-1",
                "https://service.tib.eu/ldmservice/dataset/pina-ortiz-2024-1",
                "https://service.tib.eu/ldmservice/dataset/paredes-2022-1",
                "https://service.tib.eu/ldmservice/dataset/gkatzelis-2021-1",
                "https://service.tib.eu/ldmservice/dataset/libranembid-2024-1",
                "https://service.tib.eu/ldmservice/dataset/chausson-2024-1",
                # "https://service.tib.eu/ldmservice/dataset/thiessen-2023-2",
                "https://service.tib.eu/ldmservice/dataset/bertuolgarcia-2023-1",
                "https://service.tib.eu/ldmservice/dataset/snyder-2020-1-1",
            ]

            results = []
            errors = []

            for url in URLs:
                try:
                    serializer = ScraperUrlSerializer(data={"url": url})
                    if not serializer.is_valid():
                        errors.append({"errors": serializer.errors})
                        continue

                    url_dto = ScraperUrlInputDTO(url=serializer.validated_data["url"])
                    result = self.paper_service.extract_paper(url_dto)

                    if result.success:
                        results.append({"result": True})
                    else:
                        errors.append(
                            {
                                "error": result.message or "Failed to extract paper",
                            }
                        )

                except Exception as e:
                    failure_count += 1
                    error_messages.append(f"Error adding paper from {url}: {str(e)}")

            return Response(
                {
                    "result": True,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "error_messages": error_messages,
                }
            )
        except Exception as e:
            logger.error(f"Error in add_all_papers: {str(e)}")
            return Response(
                {"error": "Failed to add papers"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
