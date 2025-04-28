"""
API viewsets for the REBORN API.

This module provides viewsets for the REST API.
"""

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from typing import Dict, Any, List, Optional
import logging

from core.infrastructure.container import Container
from core.application.interfaces.services import PaperService, SearchService
from core.application.dtos.input_dtos import (
    QueryFilterInputDTO,
    SearchInputDTO,
    ScraperUrlInputDTO,
)
from core.presentation.serializers.paper_serializers import (
    PaperSerializer,
    AuthorSerializer,
    ConceptSerializer,
    StatementSerializer,
    PaperFilterSerializer,
    SearchQuerySerializer,
    ScraperUrlSerializer,
)

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API results."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PaperViewSet(viewsets.GenericViewSet):
    """API viewset for papers."""

    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    queryset = []
    serializer_class = PaperSerializer

    def __init__(self, **kwargs):
        """Initialize the viewset."""
        super().__init__(**kwargs)
        self.paper_service = Container.get_paper_service()

    def get_queryset(self):
        """
        Return an empty queryset for schema generation.

        This method is required for OpenAPI schema generation.
        """
        # Check if this is a schema generation request
        if getattr(self, "swagger_fake_view", False):
            return []

        # For actual requests, we don't use this method
        # as we're using a service-based approach
        return []

    def get_serializer_class(self):
        """
        Return the appropriate serializer class.

        This method is required for OpenAPI schema generation.
        """
        action_serializer_map = {
            "list": PaperSerializer,
            "retrieve": PaperSerializer,
            "search_by_title": PaperSerializer,
            "query_data": PaperFilterSerializer,
            "add_paper": ScraperUrlSerializer,
            "add_all_papers": ScraperUrlSerializer,
            "get_authors": AuthorSerializer,
            "get_concepts": ConceptSerializer,
            "get_latest_statements": StatementSerializer,
            "get_latest_articles": PaperSerializer,
        }

        return action_serializer_map.get(self.action, PaperSerializer)

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance for the current action.

        This method is required for OpenAPI schema generation.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    # @method_decorator(cache_page(60 * 15))
    @method_decorator(cache_page(1 * 1))
    @method_decorator(vary_on_cookie)
    def list(self, request: Request) -> Response:
        # try:
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 10)
        print("----------paper_viewsets-----list-----------", __file__)
        # Validate and convert to integers
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            page = 1
            page_size = 10

        result = self.paper_service.get_all_papers(page, page_size)

        return Response(
            {
                "content": result.content,
                "total_elements": result.total_elements,
                "page": result.page,
                "page_size": result.page_size,
                "total_pages": result.total_pages,
                "has_next": result.has_next,
                "has_previous": result.has_previous,
            }
        )

        # except Exception as e:
        #     logger.error(f"Error in list: {str(e)}")
        #     return Response(
        #         {"error": "Failed to retrieve papers"},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )

    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def retrieve(self, request: Request, pk=None) -> Response:
        """Retrieve a paper by ID."""
        try:
            result = self.paper_service.get_paper_by_id(pk)

            if not result.success:
                return Response(
                    {"error": result.message or "Paper not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(result.result)

        except Exception as e:
            logger.error(f"Error in retrieve: {str(e)}")
            return Response(
                {"error": "Failed to retrieve paper"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def search_by_title(self, request: Request) -> Response:
        """Search papers by title."""
        try:
            title = request.query_params.get("title", "")

            if not title:
                return Response(
                    {"error": "Title parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            papers = self.paper_service.search_by_title(title)

            return Response(
                {
                    "content": papers,
                    "total_elements": len(papers),
                }
            )

        except Exception as e:
            logger.error(f"Error in search_by_title: {str(e)}")
            return Response(
                {"error": "Failed to search papers"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def query_data(self, request: Request) -> Response:
        """Query data with filters."""
        try:
            serializer = PaperFilterSerializer(data=request.data)

            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )

            # Convert to DTO
            filter_dto = QueryFilterInputDTO(
                title=serializer.validated_data.get("title"),
                start_year=serializer.validated_data.get("time_range", {}).get("start"),
                end_year=serializer.validated_data.get("time_range", {}).get("end"),
                author_ids=serializer.validated_data.get("authors", []),
                journal_names=serializer.validated_data.get("journals", []),
                concept_ids=serializer.validated_data.get("concepts", []),
                conference_names=serializer.validated_data.get("conferences", []),
                research_fields=serializer.validated_data.get("research_fields", []),
                page=serializer.validated_data.get("page", 1),
                per_page=serializer.validated_data.get("per_page", 10),
            )

            result = self.paper_service.query_data(filter_dto)

            return Response(
                {
                    "content": result.result,
                    "total_elements": result.total_count,
                    "page": filter_dto.page,
                    "per_page": filter_dto.per_page,
                    "total_pages": (result.total_count + filter_dto.per_page - 1)
                    // filter_dto.per_page,
                }
            )

        except Exception as e:
            logger.error(f"Error in query_data: {str(e)}")
            return Response(
                {"error": "Failed to query data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def all_statements(self, request: Request) -> Response:
        """Get all statements."""
        try:
            page = request.query_params.get("page", 1)
            page_size = request.query_params.get("page_size", 10)

            # Validate and convert to integers
            try:
                page = int(page)
                page_size = int(page_size)
            except ValueError:
                page = 1
                page_size = 10

            result = self.paper_service.get_all_statements(page, page_size)

            return Response(
                {
                    "content": result.content,
                    "total_elements": result.total_elements,
                    "page": result.page,
                    "page_size": result.page_size,
                    "total_pages": result.total_pages,
                }
            )

        except Exception as e:
            logger.error(f"Error in all_statements: {str(e)}")
            return Response(
                {"error": "Failed to retrieve statements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="statement")
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_statement(self, request: Request, pk=None) -> Response:
        """Get a statement by ID."""
        try:
            result = self.paper_service.get_statement(pk)

            if not result.success:
                return Response(
                    {"error": result.message or "Statement not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response({"content": result.result})

        except Exception as e:
            logger.error(f"Error in get_statement: {str(e)}")
            return Response(
                {"error": "Failed to retrieve statement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_statement_by_id(self, request: Request) -> Response:
        """Get a statement by ID."""
        try:
            statement_id = request.query_params.get("id")

            if not statement_id:
                return Response(
                    {"error": "ID parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = self.paper_service.get_statement_by_id(statement_id)

            if not result.success:
                return Response(
                    {"error": result.message or "Statement not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(result.result)

        except Exception as e:
            logger.error(f"Error in get_statement_by_id: {str(e)}")
            return Response(
                {"error": "Failed to retrieve statement"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_authors(self, request: Request) -> Response:
        """Get authors by name."""
        try:
            name = request.query_params.get("name", "")

            if not name:
                return Response([])

            authors = self.paper_service.get_authors(name)

            return Response(
                [
                    {
                        "id": author.id,
                        "name": author.label
                        or f"{author.given_name} {author.family_name}",
                    }
                    for author in authors
                ]
            )

        except Exception as e:
            logger.error(f"Error in get_authors: {str(e)}")
            return Response(
                {"error": "Failed to retrieve authors"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
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
    def latest_concepts(self, request: Request) -> Response:
        """Get latest concepts."""
        try:
            concepts = self.paper_service.get_latest_concepts()

            return Response(
                [{"id": concept.id, "name": concept.label} for concept in concepts]
            )

        except Exception as e:
            logger.error(f"Error in latest_concepts: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest concepts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_titles(self, request: Request) -> Response:
        """Get paper titles by search term."""
        try:
            title = request.query_params.get("title", "")

            if not title:
                return Response([])

            titles = self.paper_service.get_titles(title)

            return Response(titles)

        except Exception as e:
            logger.error(f"Error in get_titles: {str(e)}")
            return Response(
                {"error": "Failed to retrieve titles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_journals(self, request: Request) -> Response:
        """Get journals by name."""
        try:
            name = request.query_params.get("name", "")

            if not name:
                return Response([])

            journals = self.paper_service.get_journals(name)

            return Response(journals)

        except Exception as e:
            logger.error(f"Error in get_journals: {str(e)}")
            return Response(
                {"error": "Failed to retrieve journals"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
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
    def get_latest_statements(self, request: Request) -> Response:
        """Get latest statements with filters."""
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")

            result = self.paper_service.get_latest_statements(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            items = []
            for statement in result.content:
                author_name = ""
                if hasattr(statement, "author") and statement.author:
                    author = statement.author[0]
                    author_name = (
                        author.family_name
                        if isinstance(author, dict)
                        else author.family_name
                    )

                label = ""
                if hasattr(statement, "supports") and statement.supports:
                    if (
                        isinstance(statement.supports[0], dict)
                        and "notation" in statement.supports[0]
                    ):
                        label = statement.supports[0]["notation"]["label"]

                date = None
                journal_label = ""
                article_name = ""

                # Get paper details if available
                if hasattr(statement, "article_id") and statement.article_id:
                    paper_result = self.paper_service.get_paper_by_id(
                        statement.article_id
                    )
                    if paper_result.success and paper_result.result:
                        article = paper_result.result.get("article", {})
                        date = article.get("datePublished")
                        journal = article.get("journal", {})
                        journal_label = journal.get("label", "")
                        if not journal_label:
                            conference = article.get("conference", {})
                            journal_label = conference.get("label", "")
                        article_name = article.get("name", "")

                items.append(
                    {
                        "id": statement.statement_id or statement.id,
                        "name": label,
                        "author": author_name,
                        "date": date,
                        "journal": journal_label,
                        "article": article_name,
                    }
                )

            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_latest_statements: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest statements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_latest_articles(self, request: Request) -> Response:
        """Get latest articles with filters."""
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")

            result = self.paper_service.get_latest_articles(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            items = []
            for article in result.content:
                author_name = ""
                if hasattr(article, "author") and article.author:
                    author = article.author[0]
                    author_name = (
                        author.family_name
                        if isinstance(author, dict)
                        else author.family_name
                    )

                journal_label = ""
                if hasattr(article, "journal") and article.journal:
                    journal = article.journal
                    journal_label = (
                        journal.label
                        if hasattr(journal, "label")
                        else journal.get("label", "")
                    )

                if (
                    not journal_label
                    and hasattr(article, "conference")
                    and article.conference
                ):
                    conference = article.conference
                    journal_label = (
                        conference.label
                        if hasattr(conference, "label")
                        else conference.get("label", "")
                    )

                publisher = ""
                if hasattr(article, "publisher") and article.publisher:
                    if isinstance(article.publisher, dict):
                        publisher = article.publisher.get("label", "")

                items.append(
                    {
                        "id": article.article_id or article.id,
                        "name": article.title,
                        "author": author_name,
                        "journal": journal_label,
                        "publisher": publisher,
                        "date": article.date_published,
                    }
                )

            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_latest_articles: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest articles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_latest_keywords(self, request: Request) -> Response:
        """Get latest keywords with filters."""
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            sort_order = request.query_params.get("sort", "a-z")
            search_query = request.query_params.get("search", "")
            research_fields = request.query_params.getlist("research_fields[]")

            result = self.paper_service.get_latest_keywords(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            items = [
                {"id": concept.id, "name": concept.label} for concept in result.content
            ]

            return Response({"items": items, "total": result.total_elements})

        except Exception as e:
            logger.error(f"Error in get_latest_keywords: {str(e)}")
            return Response(
                {"error": "Failed to retrieve latest keywords"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    @method_decorator(vary_on_cookie)
    def get_latest_authors(self, request: Request) -> Response:
        """Get latest authors with filters."""
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
                    "id": author.id,
                    "doi": getattr(author, "@id", None),
                    "name": author.label or f"{author.given_name} {author.family_name}",
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
    def get_latest_journals(self, request: Request) -> Response:
        """Get latest journals with filters."""
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
    def add_paper(self, request: Request) -> Response:
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

            # List of predefined URLs
            URLs = [
                "https://service.tib.eu/ldmservice/dataset/millan-marquez-2024-1",
                "https://service.tib.eu/ldmservice/dataset/gentsch-2023-2",
                "https://service.tib.eu/ldmservice/dataset/baimuratov-2024-2",
                "https://service.tib.eu/ldmservice/dataset/perez-alvarez-2018-2",
                "https://service.tib.eu/ldmservice/dataset/pina-ortiz-2023-1",
                "https://service.tib.eu/ldmservice/dataset/akter-2023-1",
                "https://service.tib.eu/ldmservice/dataset/paredes-2022-1",
                "https://service.tib.eu/ldmservice/dataset/pina-ortiz-2024-1",
                "https://service.tib.eu/ldmservice/dataset/gkatzelis-2021-1",
            ]

            for url in URLs:
                try:
                    url_dto = ScraperUrlInputDTO(url=url)
                    result = self.paper_service.extract_paper(url_dto)

                    if result.success:
                        success_count += 1
                    else:
                        failure_count += 1
                        error_messages.append(
                            f"Failed to add paper from {url}: {result.message}"
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

    @action(detail=False, methods=["delete"])
    def delete_database(self, request: Request) -> Response:
        """Delete the database."""
        try:
            result = self.paper_service.delete_database()

            if not result.success:
                return Response(
                    {"error": result.message or "Failed to delete database"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"result": True})

        except Exception as e:
            logger.error(f"Error in delete_database: {str(e)}")
            return Response(
                {"error": "Failed to delete database"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SearchViewSet(viewsets.GenericViewSet):
    """API viewset for search."""

    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    queryset = []
    serializer_class = SearchQuerySerializer

    def __init__(self, **kwargs):
        """Initialize the viewset."""
        super().__init__(**kwargs)
        self.search_service = Container.get_search_service()

    def get_queryset(self):
        """Return an empty queryset for schema generation."""
        if getattr(self, "swagger_fake_view", False):
            return []
        return []

    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        action_serializer_map = {
            "semantic_search_statements": SearchQuerySerializer,
            "semantic_search_articles": SearchQuerySerializer,
            "delete_indices": SearchQuerySerializer,
        }
        return action_serializer_map.get(self.action, SearchQuerySerializer)

    def get_serializer(self, *args, **kwargs):
        """Get serializer instance with proper context."""
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    @action(detail=False, methods=["get"])
    def semantic_search_statements(self, request: Request) -> Response:
        """Perform semantic search on statements."""
        try:
            query = request.query_params.get("search", "")
            search_type = request.query_params.get("type", "hybrid")
            sort_order = request.query_params.get("sort", "a-z")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            research_fields = request.query_params.getlist("research_fields[]")

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = SearchInputDTO(
                query=query,
                search_type=search_type,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
                research_fields=research_fields,
            )

            result = self.search_service.semantic_search_statement(search_dto)

            return Response({"items": result.items, "total": result.total})

        except Exception as e:
            logger.error(f"Error in semantic_search_statements: {str(e)}")
            return Response(
                {"error": "Failed to perform semantic search on statements"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def semantic_search_articles(self, request: Request) -> Response:
        """Perform semantic search on articles."""
        try:
            query = request.query_params.get("search", "")
            search_type = request.query_params.get("type", "hybrid")
            sort_order = request.query_params.get("sort", "a-z")
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("limit", 10))
            research_fields = request.query_params.getlist("research_fields[]")

            if not query:
                return Response(
                    {"error": "Search query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            search_dto = SearchInputDTO(
                query=query,
                search_type=search_type,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
                research_fields=research_fields,
            )

            result = self.search_service.semantic_search_article(search_dto)

            return Response({"items": result.items, "total": result.total})

        except Exception as e:
            logger.error(f"Error in semantic_search_articles: {str(e)}")
            return Response(
                {"error": "Failed to perform semantic search on articles"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["delete"])
    def delete_indices(self, request: Request) -> Response:
        """Delete search indices."""
        try:
            result = self.search_service.delete_indices()

            if not result.success:
                return Response(
                    {"error": result.message or "Failed to delete search indices"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"result": True})

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            return Response(
                {"error": "Failed to delete search indices"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
