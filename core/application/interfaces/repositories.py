from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from core.domain.entities import (
    Paper,
    Statement,
    Author,
    Journal,
    Concept,
    ResearchField,
)


class CacheRepository(ABC):
    @abstractmethod
    def get_schema_by_type_id(self, type_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    def save_schema(self, type_id: str, schema_data: Dict[str, Any]) -> Any:
        pass


class PaperRepository(ABC):
    @abstractmethod
    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Paper], int]:
        pass

    @abstractmethod
    def find_by_id(self, paper_id: str) -> Optional[Paper]:
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> List[Paper]:
        pass

    @abstractmethod
    def query_papers(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        author_ids: Optional[List[str]] = None,
        journal_names: Optional[List[str]] = None,
        concept_ids: Optional[List[str]] = None,
        conference_names: Optional[List[str]] = None,
        title: Optional[str] = None,
        research_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Paper], int]:
        pass

    @abstractmethod
    def save(self, paper: Paper) -> Paper:
        pass

    @abstractmethod
    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
    ) -> Tuple[List[Paper], int]:
        pass

    @abstractmethod
    def delete_database(self) -> bool:
        pass

    @abstractmethod
    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        pass


class StatementRepository(ABC):
    @abstractmethod
    def find_all(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Statement], int]:
        pass

    @abstractmethod
    def find_by_id(self, statement_id: str) -> Optional[Statement]:
        pass

    @abstractmethod
    def find_by_paper_id(self, paper_id: str) -> List[Statement]:
        pass

    @abstractmethod
    def save(self, statement: Statement) -> Statement:
        pass

    @abstractmethod
    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
    ) -> Tuple[List[Statement], int]:
        pass

    @abstractmethod
    def get_semantics_statements(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        pass


class AuthorRepository(ABC):
    @abstractmethod
    def get_authors_by_name(self, name: str) -> List[Author]:
        pass

    @abstractmethod
    def save(self, author: Author) -> Author:
        pass

    @abstractmethod
    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Author], int]:
        pass


class ConceptRepository(ABC):
    @abstractmethod
    def find_by_label(self, label: str) -> List[Concept]:
        pass

    @abstractmethod
    def save(self, concept: Concept) -> Concept:
        pass

    @abstractmethod
    def get_latest_concepts(self, limit: int = 8) -> List[Concept]:
        pass

    @abstractmethod
    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Concept], int]:
        pass


class ResearchFieldRepository(ABC):
    @abstractmethod
    def get_research_fields_by_name(self, label: str) -> List[ResearchField]:
        pass

    @abstractmethod
    def save(self, research_field: ResearchField) -> ResearchField:
        pass


class JournalRepository(ABC):
    @abstractmethod
    def get_academic_publishers_by_name(self, name: str) -> List[Journal]:
        pass

    @abstractmethod
    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        pass


class SearchRepository(ABC):
    @abstractmethod
    def semantic_search_statements(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def semantic_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def keyword_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def keyword_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def hybrid_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def hybrid_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_statements(self, statements: List[Dict[str, str]]) -> bool:
        pass

    @abstractmethod
    def add_articles(self, articles: List[Dict[str, str]]) -> bool:
        pass

    @abstractmethod
    def delete_indices(self) -> bool:
        pass

    @abstractmethod
    def delete_article(self, article_id: str) -> bool:
        pass

    @abstractmethod
    def delete_statement(self, statement_id: str) -> bool:
        pass

    @abstractmethod
    def update_article(self, article: Dict[str, str]) -> bool:
        pass

    @abstractmethod
    def update_statement(self, statement: Dict[str, str]) -> bool:
        pass
