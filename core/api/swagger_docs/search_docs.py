from drf_yasg import openapi

get_latest_articles_docs = {
    "operation_summary": "Get latest articles with advanced search options",
    "operation_description": (
        "Retrieves the latest articles with filtering, pagination, and sorting options.\n\n"
        "## Search Types\n"
        "- **hybrid**: Combines semantic and keyword search for best results (default)\n"
        "- **semantic**: Uses AI-based semantic understanding (Weaviate) to find articles based on meaning\n"
        "- **full-text**: Uses traditional PostgreSQL full-text search with ranking\n"
    ),
    "manual_parameters": [
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
        openapi.Parameter(
            "limit",
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10,
        ),
        openapi.Parameter(
            "sort",
            openapi.IN_QUERY,
            description="Sort order",
            type=openapi.TYPE_STRING,
            enum=["a-z", "z-a", "newest"],
            default="a-z",
        ),
        openapi.Parameter(
            "search",
            openapi.IN_QUERY,
            description="Search query",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            "search_type",
            openapi.IN_QUERY,
            description="Type of search to perform: hybrid, semantic, or full-text",
            type=openapi.TYPE_STRING,
            enum=["hybrid", "semantic", "full-text"],
            default="hybrid",
        ),
        openapi.Parameter(
            "research_fields[]",
            openapi.IN_QUERY,
            description="List of research field IDs to filter by",
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            collectionFormat="multi",
        ),
    ],
    "responses": {
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "article_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "author": openapi.Schema(type=openapi.TYPE_STRING),
                                "scientific_venue": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "date_published": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "search_type_used": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="The search type that was used for this query",
                                ),
                            },
                        ),
                    ),
                    "total": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        400: openapi.Response(description="Bad request"),
        500: openapi.Response(description="Internal server error"),
    },
}

get_latest_statements_docs = {
    "operation_summary": "Get latest statements with advanced search options",
    "operation_description": (
        "Retrieves the latest statements with filtering, pagination, and sorting options.\n\n"
        "## Search Types\n"
        "- **hybrid**: Combines semantic and keyword search for best results (default)\n"
        "- **semantic**: Uses AI-based semantic understanding (Weaviate) to find statements based on meaning\n"
        "- **full-text**: Uses traditional PostgreSQL full-text search with ranking\n"
    ),
    "manual_parameters": [
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1,
        ),
        openapi.Parameter(
            "limit",
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10,
        ),
        openapi.Parameter(
            "sort",
            openapi.IN_QUERY,
            description="Sort order",
            type=openapi.TYPE_STRING,
            enum=["a-z", "z-a", "newest"],
            default="a-z",
        ),
        openapi.Parameter(
            "search",
            openapi.IN_QUERY,
            description="Search query",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            "search_type",
            openapi.IN_QUERY,
            description="Type of search to perform: hybrid, semantic, or full-text",
            type=openapi.TYPE_STRING,
            enum=["hybrid", "semantic", "full-text"],
            default="hybrid",
        ),
        openapi.Parameter(
            "research_fields[]",
            openapi.IN_QUERY,
            description="List of research field IDs to filter by",
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING),
            collectionFormat="multi",
        ),
    ],
    "responses": {
        200: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "statement_id": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                                "author": openapi.Schema(type=openapi.TYPE_STRING),
                                "scientific_venue": openapi.Schema(
                                    type=openapi.TYPE_STRING
                                ),
                                "article": openapi.Schema(type=openapi.TYPE_STRING),
                                "date_published": openapi.Schema(
                                    type=openapi.TYPE_INTEGER
                                ),
                                "search_type_used": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="The search type that was used for this query",
                                ),
                            },
                        ),
                    ),
                    "total": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
        400: openapi.Response(description="Bad request"),
        500: openapi.Response(description="Internal server error"),
    },
}
