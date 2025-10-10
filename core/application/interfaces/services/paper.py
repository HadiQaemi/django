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
    @abstractmethod
    def get_all_papers(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        pass

    @abstractmethod
    def get_paper_by_id(self, paper_id: str) -> CommonResponseDTO:
        pass

    @abstractmethod
    def get_all_statements(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> List[PaperOutputDTO]:
        pass

    @abstractmethod
    def query_data(self, query_filter: QueryFilterInputDTO) -> PaginatedResponseDTO:
        pass

    @abstractmethod
    def get_article_statement(self, statement_id: str) -> CommonResponseDTO:
        pass

    @abstractmethod
    def get_authors(self, search_term: str) -> List[AuthorOutputDTO]:
        pass

    @abstractmethod
    def get_concepts(self, search_term: str) -> List[ConceptOutputDTO]:
        pass

    @abstractmethod
    def get_latest_concepts(self) -> List[ConceptOutputDTO]:
        pass

    @abstractmethod
    def get_titles(self, search_term: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_journals(self, search_term: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_research_fields(self, search_term: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_statement(self, statement_id: str) -> CommonResponseDTO:
        pass

    @abstractmethod
    def get_paper(self, paper_id: str) -> CommonResponseDTO:
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
        pass

    @abstractmethod
    def extract_paper(self, url_dto: ScraperUrlInputDTO) -> CommonResponseDTO:
        pass

    @abstractmethod
    def delete_database(self) -> CommonResponseDTO:
        pass

    @abstractmethod
    def delete_article(self, article_id: str) -> CommonResponseDTO:
        pass
