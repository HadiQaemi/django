from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.application.dtos.input_dtos import QueryFilterInputDTO, ScraperUrlInputDTO
from core.application.dtos.output_dtos import (
    AuthorOutputDTO,
    CommonResponseDTO,
    ConceptOutputDTO,
    PaginatedResponseDTO,
    PaperOutputDTO,
)


class PaperService(ABC):
    """Service interface for paper-related operations."""

    @abstractmethod
    def get_all_papers(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all papers with pagination."""
        pass

    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper by its ID."""
        pass

    @abstractmethod
    def get_all_statements(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all statements with pagination."""
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> List[PaperOutputDTO]:
        """Search papers by title."""
        pass

    @abstractmethod
    def query_data(self, query_filter: QueryFilterInputDTO) -> PaginatedResponseDTO:
        """Query data with filters."""
        pass

    @abstractmethod
    def get_article_statement(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement by its ID."""
        pass

    @abstractmethod
    def get_authors(self, search_term: str) -> List[AuthorOutputDTO]:
        """Get authors by search term."""
        pass

    @abstractmethod
    def get_concepts(self, search_term: str) -> List[ConceptOutputDTO]:
        """Get concepts by search term."""
        pass

    @abstractmethod
    def get_latest_concepts(self) -> List[ConceptOutputDTO]:
        """Get latest concepts."""
        pass

    @abstractmethod
    def get_titles(self, search_term: str) -> List[Dict[str, Any]]:
        """Get paper titles by search term."""
        pass

    @abstractmethod
    def get_journals(self, search_term: str) -> List[Dict[str, Any]]:
        """Get journals by search term."""
        pass

    @abstractmethod
    def get_research_fields(self, search_term: str) -> List[Dict[str, Any]]:
        """Get research fields by search term."""
        pass

    @abstractmethod
    def get_statement(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement with related data."""
        pass

    @abstractmethod
    def get_paper(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper with related data."""
        pass

    @abstractmethod
    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest statements with filters."""
        pass

    @abstractmethod
    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "ASC",
        sort_by: str = "alphabet",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
        resource_type: str = "loom",

        year_range: Any = None,
        authors: Optional[List[str]] = None,
        scientific_venues: Optional[List[str]] = None,
        concepts: Optional[List[str]] = None,
    ) -> PaginatedResponseDTO:
        """Get latest articles with filters."""
        pass

    @abstractmethod
    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest keywords with filters."""
        pass

    @abstractmethod
    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest authors with filters."""
        pass

    @abstractmethod
    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest journals with filters."""
        pass

    @abstractmethod
    def extract_paper(self, url_dto: ScraperUrlInputDTO) -> CommonResponseDTO:
        """Extract a paper from a URL."""
        pass

    @abstractmethod
    def delete_database(self) -> CommonResponseDTO:
        """Delete the database."""
        pass
