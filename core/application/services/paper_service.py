"""
Paper service implementation for the REBORN API.

This service handles all paper-related operations.
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from django.core.cache import cache
from django.conf import settings

from core.application.interfaces.services import PaperService as PaperServiceInterface
from core.application.interfaces.repositories import (
    PaperRepository,
    StatementRepository,
    AuthorRepository,
    ConceptRepository,
    ResearchFieldRepository,
    JournalRepository,
)
from core.application.dtos.input_dtos import (
    PaperInputDTO,
    QueryFilterInputDTO,
    ScraperUrlInputDTO,
)
from core.application.dtos.output_dtos import (
    PaperOutputDTO,
    ShortPaperOutputDTO,
    StatementOutputDTO,
    AuthorOutputDTO,
    ShortAuthorOutputDTO,
    ShortResearchFieldOutputDTO,
    ConceptOutputDTO,
    CommonResponseDTO,
    PaginatedResponseDTO,
    ResearchFieldOutputDTO,
)
from core.domain.exceptions import (
    EntityNotFound,
    InvalidInput,
    ScraperError,
    DatabaseError,
)
from core.infrastructure.scrapers.node_extractor import NodeExtractor

logger = logging.getLogger(__name__)


class PaperServiceImpl(PaperServiceInterface):
    """Implementation of the paper service."""

    def __init__(
        self,
        paper_repository: PaperRepository,
        statement_repository: StatementRepository,
        author_repository: AuthorRepository,
        concept_repository: ConceptRepository,
        research_field_repository: ResearchFieldRepository,
        journal_repository: JournalRepository,
    ):
        self.paper_repository = paper_repository
        self.statement_repository = statement_repository
        self.author_repository = author_repository
        self.concept_repository = concept_repository
        self.research_field_repository = research_field_repository
        self.journal_repository = journal_repository
        self.scraper = NodeExtractor()

    def get_all_papers(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all papers with pagination."""
        # cache_key = f"all_papers_{page}_{page_size}"
        # cached_result = cache.get(cache_key)
        print("------------get_all_papers------------", __file__)
        # if cached_result:
        #     return cached_result

        # try:
        papers, total = self.paper_repository.find_all(page, page_size)
        print("----------papers----------", __file__)
        print(papers[0].id)
        # print(papers[0].name)
        # print(papers[0].authors)
        print(papers[0])
        print("----------papers----------", __file__)
        result = PaginatedResponseDTO(
            content=[self._map_paper_to_dto(paper) for paper in papers],
            total_elements=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )

        # Cache for 15 minutes
        # cache.set(cache_key, result, settings.CACHE_TTL)
        return result

        # except Exception as e:
        #     logger.error(f"Error in get_all_papers: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve papers: {str(e)}")

    def get_paper_by_id(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper by its ID."""
        cache_key = f"paper_{paper_id}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            paper = self.paper_repository.find_by_id(paper_id)

            if paper:
                statements = self.statement_repository.find_by_paper_id(paper_id)
                paper_dto = self._map_paper_to_dto(paper)

                for statement in statements:
                    statement_dto = self._map_statement_to_dto(statement)
                    paper_dto.statements.append(statement_dto)

                result = CommonResponseDTO(
                    success=True,
                    result={
                        "article": paper_dto,
                        "statements": [s for s in paper_dto.statements],
                    },
                    total_count=len(paper_dto.statements),
                )

                # Cache for 15 minutes
                cache.set(cache_key, result, settings.CACHE_TTL)
                return result

            return CommonResponseDTO(
                success=False, message=f"Paper with ID {paper_id} not found"
            )

        except Exception as e:
            logger.error(f"Error in get_paper_by_id: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve paper: {str(e)}"
            )

    def get_all_statements(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all statements with pagination."""
        cache_key = f"all_statements_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            statements, total = self.statement_repository.find_all(page, page_size)

            result = PaginatedResponseDTO(
                content=[
                    self._map_statement_to_dto(statement) for statement in statements
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_all_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements: {str(e)}")

    def search_by_title(self, title: str) -> List[PaperOutputDTO]:
        """Search papers by title."""
        try:
            papers = self.paper_repository.search_by_title(title)
            return [self._map_paper_to_dto(paper) for paper in papers]

        except Exception as e:
            logger.error(f"Error in search_by_title: {str(e)}")
            raise DatabaseError(f"Failed to search papers: {str(e)}")

    def query_data(self, query_filter: QueryFilterInputDTO) -> CommonResponseDTO:
        """Query data with filters."""
        try:
            papers, total = self.paper_repository.query_papers(
                start_year=query_filter.start_year,
                end_year=query_filter.end_year,
                author_ids=query_filter.author_ids,
                journal_names=query_filter.journal_names,
                concept_ids=query_filter.concept_ids,
                conference_names=query_filter.conference_names,
                title=query_filter.title,
                research_fields=query_filter.research_fields,
                page=query_filter.page,
                page_size=query_filter.per_page,
            )

            # Group articles by ID
            grouped_data = {}
            for paper in papers:
                if paper.id not in grouped_data:
                    grouped_data[paper.id] = self._map_paper_to_dto(paper)

            return CommonResponseDTO(
                success=True, result=grouped_data, total_count=total
            )

        except Exception as e:
            logger.error(f"Error in query_data: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to query data: {str(e)}"
            )

    def get_statement_by_id(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement by its ID."""
        try:
            statement = self.statement_repository.find_by_id(statement_id)

            if statement:
                statement_dto = self._map_statement_to_dto(statement)

                return CommonResponseDTO(
                    success=True, result={"statement": statement_dto}, total_count=1
                )

            return CommonResponseDTO(
                success=False, message=f"Statement with ID {statement_id} not found"
            )

        except Exception as e:
            logger.error(f"Error in get_statement_by_id: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve statement: {str(e)}"
            )

    def get_authors(self, search_term: str) -> List[AuthorOutputDTO]:
        """Get authors by search term."""
        try:
            authors = self.author_repository.find_by_name(search_term)
            return [
                AuthorOutputDTO(
                    id=author.id,
                    given_name=author.given_name,
                    family_name=author.family_name,
                    label=author.label or f"{author.given_name} {author.family_name}",
                )
                for author in authors
            ]

        except Exception as e:
            logger.error(f"Error in get_authors: {str(e)}")
            return []

    def get_concepts(self, search_term: str) -> List[ConceptOutputDTO]:
        """Get concepts by search term."""
        try:
            concepts = self.concept_repository.find_by_label(search_term)
            return [
                ConceptOutputDTO(
                    id=concept.id, label=concept.label, identifier=concept.identifier
                )
                for concept in concepts
            ]

        except Exception as e:
            logger.error(f"Error in get_concepts: {str(e)}")
            return []

    def get_latest_concepts(self) -> List[ConceptOutputDTO]:
        """Get latest concepts."""
        try:
            concepts = self.concept_repository.get_latest_concepts()
            return [
                ConceptOutputDTO(
                    id=concept.id, label=concept.label, identifier=concept.identifier
                )
                for concept in concepts
            ]

        except Exception as e:
            logger.error(f"Error in get_latest_concepts: {str(e)}")
            return []

    def get_titles(self, search_term: str) -> List[Dict[str, Any]]:
        """Get paper titles by search term."""
        try:
            papers = self.paper_repository.search_by_title(search_term)
            return [{"id": paper.id, "name": paper.title} for paper in papers]

        except Exception as e:
            logger.error(f"Error in get_titles: {str(e)}")
            return []

    def get_journals(self, search_term: str) -> List[Dict[str, Any]]:
        """Get journals by search term."""
        try:
            journals = self.journal_repository.find_by_name(search_term)
            return [
                {"id": journal.get("id", ""), "name": journal.get("label", "")}
                for journal in journals
            ]

        except Exception as e:
            logger.error(f"Error in get_journals: {str(e)}")
            return []

    def get_research_fields(self, search_term: str) -> List[Dict[str, Any]]:
        """Get research fields by search term."""
        try:
            research_fields = self.research_field_repository.find_by_label(search_term)
            return [{"id": rf.id, "name": rf.label} for rf in research_fields]

        except Exception as e:
            logger.error(f"Error in get_research_fields: {str(e)}")
            return []

    def get_statement(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement with related data."""
        try:
            statements = self.statement_repository.find_by_id(statement_id)

            # Group statements by article ID
            grouped_data = {}
            if statements:
                # This is specific to the original implementation structure
                paper_id = statements.article_id
                if paper_id not in grouped_data:
                    grouped_data[paper_id] = self._map_statement_to_dto(statements)

            return CommonResponseDTO(
                success=True, result=grouped_data, total_count=len(grouped_data)
            )

        except Exception as e:
            logger.error(f"Error in get_statement: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve statement: {str(e)}"
            )

    def get_paper(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper with related data."""
        try:
            paper = self.paper_repository.find_by_id(paper_id)

            # Group statements by article ID
            grouped_data = {}
            if paper:
                # Get statements for this paper
                statements = self.statement_repository.find_by_paper_id(paper.id)
                paper_dto = self._map_paper_to_dto(paper)

                for statement in statements:
                    statement_dto = self._map_statement_to_dto(statement)
                    paper_dto.statements.append(statement_dto)

                grouped_data[paper.id] = paper_dto

            return CommonResponseDTO(
                success=True, result=grouped_data, total_count=len(grouped_data)
            )

        except Exception as e:
            logger.error(f"Error in get_paper: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve paper: {str(e)}"
            )

    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest statements with filters."""
        cache_key = f"latest_statements_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            statements, total = self.statement_repository.get_latest_statements(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[
                    self._map_statement_to_dto(statement) for statement in statements
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest statements: {str(e)}")

    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest articles with filters."""
        cache_key = f"latest_articles_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            papers, total = self.paper_repository.get_latest_articles(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[self._map_paper_to_dto(paper) for paper in papers],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest articles: {str(e)}")

    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest keywords with filters."""
        cache_key = f"latest_keywords_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            concepts, total = self.concept_repository.get_latest_keywords(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[
                    ConceptOutputDTO(
                        id=concept.id,
                        label=concept.label,
                        identifier=concept.identifier,
                    )
                    for concept in concepts
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_keywords: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest keywords: {str(e)}")

    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest authors with filters."""
        cache_key = f"latest_authors_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            authors, total = self.author_repository.get_latest_authors(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[
                    AuthorOutputDTO(
                        id=author.id,
                        given_name=author.given_name,
                        family_name=author.family_name,
                        label=author.label
                        or f"{author.given_name} {author.family_name}",
                    )
                    for author in authors
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_authors: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest authors: {str(e)}")

    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest journals with filters."""
        cache_key = f"latest_journals_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result

        try:
            journals, total = self.journal_repository.get_latest_journals(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            content = []
            for journal in journals:
                if isinstance(journal, dict):
                    content.append(
                        {
                            "id": journal.get("id", ""),
                            "name": journal.get("label", ""),
                            "publisher": journal.get("publisher", {}).get("label", "")
                            if journal.get("publisher")
                            else "",
                        }
                    )

            result = PaginatedResponseDTO(
                content=content,
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest journals: {str(e)}")

    def extract_paper(self, url_dto: ScraperUrlInputDTO) -> CommonResponseDTO:
        # """Extract a paper from a URL."""
        # try:
        url = str(url_dto.url)
        self.scraper.set_url(url)
        json_files = self.scraper.all_json_files()
        ro_crate = self.scraper.load_json_from_url(json_files["ro-crate-metadata.json"])
        print(json_files)
        self.paper_repository.add_article(ro_crate, json_files)
        # Invalidate relevant caches
        cache.delete_pattern("all_papers_*")
        cache.delete_pattern("latest_articles_*")

        return CommonResponseDTO(
            success=True, message="Paper extracted and saved successfully"
        )

    # except Exception as e:
    #     logger.error(f"Error in extract_paper: {str(e)}")
    #     return CommonResponseDTO(
    #         success=False, message=f"Failed to extract paper ssss: {str(e)}"
    #     )

    def delete_database(self) -> CommonResponseDTO:
        """Delete the database."""
        try:
            success = self.paper_repository.delete_database()

            # Clear all caches
            cache.clear()

            return CommonResponseDTO(
                success=success,
                message="Database deleted successfully"
                if success
                else "Failed to delete database",
            )

        except Exception as e:
            logger.error(f"Error in delete_database: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to delete database: {str(e)}"
            )

    def _map_paper_to_dto(self, paper) -> ShortPaperOutputDTO:
        """Map a paper entity to its DTO."""
        authors = []
        print("----------_map_paper_to_dto------------", __file__)
        print(paper)
        for author in paper.authors:
            if isinstance(author, dict):
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.get("label", ""),
                    )
                )
            else:
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.label,
                    )
                )

        research_fields = []
        # for rf in paper.research_fields:
        #     if isinstance(rf, dict):
        #         research_fields.append(
        #             ShortResearchFieldOutputDTO(label=rf.get("label", ""))
        #         )
        #     else:
        #         research_fields.append(ShortResearchFieldOutputDTO(label=rf.label))
        return ShortPaperOutputDTO(
            id=paper.id,
            name=paper.name,
            authors=authors,
        )

    def _map_statement_to_dto(self, statement) -> StatementOutputDTO:
        """Map a statement entity to its DTO."""
        authors = []
        for author in statement.author:
            if isinstance(author, dict):
                authors.append(
                    AuthorOutputDTO(
                        id=author.get("id", ""),
                        given_name=author.get("given_name", ""),
                        family_name=author.get("family_name", ""),
                        label=author.get("label", ""),
                    )
                )
            else:
                authors.append(
                    AuthorOutputDTO(
                        id=author.id,
                        given_name=author.given_name,
                        family_name=author.family_name,
                        label=author.label,
                    )
                )

        return StatementOutputDTO(
            id=statement.id,
            statement_id=statement.statement_id or statement.id,
            content=statement.content,
            author=authors,
            article_id=statement.article_id,
            supports=statement.supports,
            notation=None,  # Will be filled separately if needed
            created_at=statement.created_at,
            updated_at=statement.updated_at,
        )
