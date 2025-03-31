"""
Search service implementation for the REBORN API.

This service handles all search-related operations.
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from django.core.cache import cache
from django.conf import settings
from sentence_transformers import CrossEncoder

from core.application.interfaces.services import SearchService as SearchServiceInterface
from core.application.interfaces.repositories import (
    SearchRepository,
    StatementRepository,
    PaperRepository,
)
from core.application.dtos.input_dtos import SearchInputDTO
from core.application.dtos.output_dtos import (
    SearchResultsDTO,
    SearchResultItemDTO,
    CommonResponseDTO,
)
from core.domain.exceptions import SearchEngineError

logger = logging.getLogger(__name__)


class SearchServiceImpl(SearchServiceInterface):
    """Implementation of the search service."""

    def __init__(
        self,
        search_repository: SearchRepository,
        statement_repository: StatementRepository,
        paper_repository: PaperRepository,
    ):
        self.search_repository = search_repository
        self.statement_repository = statement_repository
        self.paper_repository = paper_repository
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def semantic_search_statement(self, search_dto: SearchInputDTO) -> SearchResultsDTO:
        """Perform semantic search on statements."""
        cache_key = f"semantic_search_statement_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            query = search_dto.query
            search_type = search_dto.search_type
            sort_order = search_dto.sort_order
            page = search_dto.page
            page_size = search_dto.page_size

            if search_type == "keyword":
                # Use repository query for keyword search
                statements, total = self.statement_repository.get_latest_statements(
                    research_fields=search_dto.research_fields,
                    search_query=query,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )

                items = []
                for statement in statements:
                    author_name = (
                        statement.author[0].family_name if statement.author else ""
                    )
                    label = statement.notation.label if statement.notation else ""
                    journal_label = ""

                    # Extract paper details if available
                    paper = self.paper_repository.find_by_id(statement.article_id)
                    if paper:
                        journal_label = paper.journal.label if paper.journal else ""
                        if not journal_label and paper.conference:
                            journal_label = paper.conference.label

                    items.append(
                        SearchResultItemDTO(
                            id=statement.statement_id or statement.id,
                            name=label,
                            author=author_name,
                            date=paper.date_published if paper else None,
                            journal=journal_label,
                            article=paper.title if paper else "",
                        )
                    )

                result = SearchResultsDTO(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=math.ceil(total / page_size if total > 0 else 1),
                )

                cache.set(cache_key, result, settings.CACHE_TTL)
                return result

            elif search_type in ["semantic", "hybrid"]:
                # Use semantic or hybrid search
                if search_type == "semantic":
                    search_results = self.search_repository.semantic_search_statements(
                        query
                    )
                    statement_ids = [
                        result.get("id")
                        for result in search_results
                        if result.get("id")
                    ]
                else:  # hybrid
                    search_results, statement_ids = (
                        self.search_repository.hybrid_search_statements(query)
                    )

                # Get statements from database
                statements, total = self.statement_repository.get_semantics_statements(
                    ids=statement_ids,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )

                # Format search results
                temp_statements = statements

                if search_type == "hybrid":
                    # Rerank using cross-encoder
                    pairs = [
                        [query, statement.notation.label if statement.notation else ""]
                        for statement in temp_statements
                    ]
                    scores = self.reranker.predict(pairs)

                    # Sort by score descending
                    ranked_indices = sorted(
                        range(len(scores)), key=lambda i: scores[i], reverse=True
                    )
                    temp_statements = [temp_statements[i] for i in ranked_indices]

                items = []
                for statement in temp_statements:
                    author_name = (
                        statement.author[0].family_name if statement.author else ""
                    )
                    label = statement.notation.label if statement.notation else ""
                    journal_label = ""

                    # Extract paper details if available
                    paper = self.paper_repository.find_by_id(statement.article_id)
                    if paper:
                        journal_label = paper.journal.label if paper.journal else ""
                        if not journal_label and paper.conference:
                            journal_label = paper.conference.label

                    items.append(
                        SearchResultItemDTO(
                            id=statement.statement_id or statement.id,
                            name=label,
                            author=author_name,
                            date=paper.date_published if paper else None,
                            journal=journal_label,
                            article=paper.title if paper else "",
                        )
                    )

                result = SearchResultsDTO(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=math.ceil(total / page_size if total > 0 else 1),
                )

                cache.set(cache_key, result, settings.CACHE_TTL)
                return result

            else:
                logger.error(f"Invalid search type: {search_type}")
                return SearchResultsDTO(
                    items=[], total=0, page=page, page_size=page_size, total_pages=0
                )

        except Exception as e:
            logger.error(f"Error in semantic_search_statement: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform semantic search on statements: {str(e)}"
            )

    def semantic_search_article(self, search_dto: SearchInputDTO) -> SearchResultsDTO:
        """Perform semantic search on articles."""
        cache_key = f"semantic_search_article_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            query = search_dto.query
            search_type = search_dto.search_type
            sort_order = search_dto.sort_order
            page = search_dto.page
            page_size = search_dto.page_size

            if search_type == "keyword":
                # Use repository query for keyword search
                papers, total = self.paper_repository.get_latest_articles(
                    research_fields=search_dto.research_fields,
                    search_query=query,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )

                items = []
                for paper in papers:
                    author_name = paper.author[0].family_name if paper.author else ""
                    journal_label = paper.journal.label if paper.journal else ""
                    if not journal_label and paper.conference:
                        journal_label = paper.conference.label
                    publisher = (
                        paper.publisher.get("label", "") if paper.publisher else ""
                    )

                    items.append(
                        SearchResultItemDTO(
                            id=paper.article_id or paper.id,
                            name=paper.title,
                            author=author_name,
                            date=paper.date_published,
                            journal=journal_label,
                            publisher=publisher,
                        )
                    )

                result = SearchResultsDTO(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=math.ceil(total / page_size if total > 0 else 1),
                )

                cache.set(cache_key, result, settings.CACHE_TTL)
                return result

            elif search_type in ["semantic", "hybrid"]:
                # Use semantic or hybrid search
                if search_type == "semantic":
                    search_results = self.search_repository.semantic_search_articles(
                        query
                    )
                    article_ids = [
                        result.get("id")
                        for result in search_results
                        if result.get("id")
                    ]
                else:  # hybrid
                    search_results, article_ids = (
                        self.search_repository.hybrid_search_articles(query)
                    )

                # Get articles from database
                papers, total = self.paper_repository.get_semantics_articles(
                    ids=article_ids,
                    sort_order=sort_order,
                    page=page,
                    page_size=page_size,
                )

                # Format search results
                temp_papers = papers

                if search_type == "hybrid":
                    # Rerank using cross-encoder
                    pairs = [[query, paper.abstract] for paper in temp_papers]
                    scores = self.reranker.predict(pairs)

                    # Sort by score descending
                    ranked_indices = sorted(
                        range(len(scores)), key=lambda i: scores[i], reverse=True
                    )
                    temp_papers = [temp_papers[i] for i in ranked_indices]

                items = []
                for paper in temp_papers:
                    author_name = paper.author[0].family_name if paper.author else ""
                    journal_label = paper.journal.label if paper.journal else ""
                    if not journal_label and paper.conference:
                        journal_label = paper.conference.label
                    publisher = (
                        paper.publisher.get("label", "") if paper.publisher else ""
                    )

                    items.append(
                        SearchResultItemDTO(
                            id=paper.article_id or paper.id,
                            name=paper.title,
                            author=author_name,
                            date=paper.date_published,
                            journal=journal_label,
                            publisher=publisher,
                        )
                    )

                result = SearchResultsDTO(
                    items=items,
                    total=total,
                    page=page,
                    page_size=page_size,
                    total_pages=math.ceil(total / page_size if total > 0 else 1),
                )

                cache.set(cache_key, result, settings.CACHE_TTL)
                return result

            else:
                logger.error(f"Invalid search type: {search_type}")
                return SearchResultsDTO(
                    items=[], total=0, page=page, page_size=page_size, total_pages=0
                )

        except Exception as e:
            logger.error(f"Error in semantic_search_article: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform semantic search on articles: {str(e)}"
            )

    def delete_indices(self) -> CommonResponseDTO:
        """Delete search indices."""
        try:
            success = self.search_repository.delete_indices()

            return CommonResponseDTO(
                success=success,
                message="Search indices deleted successfully"
                if success
                else "Failed to delete search indices",
            )

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to delete search indices: {str(e)}"
            )
