from django.urls import path, include
from rest_framework.routers import DefaultRouter

from core.presentation.viewsets.paper_viewsets import PaperViewSet, SearchViewSet

# Create a router for viewsets
router = DefaultRouter()
router.register(r"articles", PaperViewSet, basename="paper")
router.register(r"search", SearchViewSet, basename="search")

# URL patterns for API v1
urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Papers API
    # path("all_paper/", PaperViewSet.as_view({"get": "list"}), name="all_paper"),
    # path(
    #     "all-statements/",
    #     PaperViewSet.as_view({"get": "all_statements"}),
    #     name="all-statements",
    # ),
    # path("search/", PaperViewSet.as_view({"get": "search_by_title"}), name="search"),
    # path("paper/", PaperViewSet.as_view({"get": "retrieve"}), name="paper"),
    # path(
    #     "statement/",
    #     PaperViewSet.as_view({"get": "get_statement_by_id"}),
    #     name="statement",
    # ),
    # path(
    #     "get-statement/",
    #     PaperViewSet.as_view({"get": "get_statement"}),
    #     name="get-statement",
    # ),
    # path("get-paper/", PaperViewSet.as_view({"get": "retrieve"}), name="get-paper"),
    # path(
    #     "get-authors/", PaperViewSet.as_view({"get": "get_authors"}), name="get-authors"
    # ),
    # path(
    #     "get-concepts/",
    #     PaperViewSet.as_view({"get": "get_concepts"}),
    #     name="get-concepts",
    # ),
    # path(
    #     "latest-concepts/",
    #     PaperViewSet.as_view({"get": "latest_concepts"}),
    #     name="latest-concepts",
    # ),
    # path("titles/", PaperViewSet.as_view({"get": "get_titles"}), name="titles"),
    # path(
    #     "get-journals/",
    #     PaperViewSet.as_view({"get": "get_journals"}),
    #     name="get-journals",
    # ),
    # path(
    #     "research_fields/",
    #     PaperViewSet.as_view({"get": "get_research_fields"}),
    #     name="research_fields",
    # ),
    # path(
    #     "statements/",
    #     PaperViewSet.as_view({"get": "get_latest_statements"}),
    #     name="statements",
    # ),
    # path(
    #     "articles/",
    #     PaperViewSet.as_view({"get": "get_latest_articles"}),
    #     name="articles",
    # ),
    # path(
    #     "keywords/",
    #     PaperViewSet.as_view({"get": "get_latest_keywords"}),
    #     name="keywords",
    # ),
    # path(
    #     "authors/", PaperViewSet.as_view({"get": "get_latest_authors"}), name="authors"
    # ),
    # path(
    #     "journals/",
    #     PaperViewSet.as_view({"get": "get_latest_journals"}),
    #     name="journals",
    # ),
    # path(
    #     "filter-statement/",
    #     PaperViewSet.as_view({"post": "query_data"}),
    #     name="filter-statement",
    # ),
    # path("query-data/", PaperViewSet.as_view({"get": "query_data"}), name="query-data"),
    # path("add-paper/", PaperViewSet.as_view({"post": "add_paper"}), name="add-paper"),
    # path(
    #     "add-all-papers/",
    #     PaperViewSet.as_view({"post": "add_all_papers"}),
    #     name="add-all-papers",
    # ),
    # path(
    #     "delete_database/",
    #     PaperViewSet.as_view({"delete": "delete_database"}),
    #     name="delete_database",
    # ),
    # # Search API
    # path(
    #     "semantic_search_statements/",
    #     SearchViewSet.as_view({"get": "semantic_search_statements"}),
    #     name="semantic_search_statements",
    # ),
    # path(
    #     "semantic_search_articles/",
    #     SearchViewSet.as_view({"get": "semantic_search_articles"}),
    #     name="semantic_search_articles",
    # ),
    # path(
    #     "delete_indices/",
    #     SearchViewSet.as_view({"delete": "delete_indices"}),
    #     name="delete_indices",
    # ),
]
