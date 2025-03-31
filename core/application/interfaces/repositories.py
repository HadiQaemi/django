"""
Repository interfaces for the REBORN API.

These interfaces define the contract for data access in the application.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from core.domain.entities import (
    Paper,
    Contribution,
    Statement,
    Author,
    Concept,
    ResearchField,
)


class PaperRepository(ABC):
    """Repository interface for Paper entities."""

    @abstractmethod
    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Paper], int]:
        """Find all papers with pagination."""
        pass

    @abstractmethod
    def find_by_id(self, paper_id: str) -> Optional[Paper]:
        """Find a paper by its ID."""
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> List[Paper]:
        """Search papers by title."""
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
        """Query papers with filters."""
        pass

    @abstractmethod
    def save(self, paper: Paper) -> Paper:
        """Save a paper."""
        pass

    @abstractmethod
    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Paper], int]:
        """Get latest articles with filters."""
        pass

    @abstractmethod
    def delete_database(self) -> bool:
        """Delete the database."""
        pass

    @abstractmethod
    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        """Add an article from scraped data."""
        pass


class StatementRepository(ABC):
    """Repository interface for Statement entities."""

    @abstractmethod
    def find_all(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Statement], int]:
        """Find all statements with pagination."""
        pass

    @abstractmethod
    def find_by_id(self, statement_id: str) -> Optional[Statement]:
        """Find a statement by its ID."""
        pass

    @abstractmethod
    def find_by_paper_id(self, paper_id: str) -> List[Statement]:
        """Find statements by paper ID."""
        pass

    @abstractmethod
    def save(self, statement: Statement) -> Statement:
        """Save a statement."""
        pass

    @abstractmethod
    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        """Get latest statements with filters."""
        pass

    @abstractmethod
    def get_semantics_statements(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        """Get statements by IDs from semantic search."""
        pass


class AuthorRepository(ABC):
    """Repository interface for Author entities."""

    @abstractmethod
    def find_by_name(self, name: str) -> List[Author]:
        """Find authors by name."""
        pass

    @abstractmethod
    def save(self, author: Author) -> Author:
        """Save an author."""
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
        """Get latest authors with filters."""
        pass


class ConceptRepository(ABC):
    """Repository interface for Concept entities."""

    @abstractmethod
    def find_by_label(self, label: str) -> List[Concept]:
        """Find concepts by label."""
        pass

    @abstractmethod
    def save(self, concept: Concept) -> Concept:
        """Save a concept."""
        pass

    @abstractmethod
    def get_latest_concepts(self, limit: int = 8) -> List[Concept]:
        """Get latest concepts."""
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
        """Get latest keywords with filters."""
        pass


class ResearchFieldRepository(ABC):
    """Repository interface for ResearchField entities."""

    @abstractmethod
    def find_by_label(self, label: str) -> List[ResearchField]:
        """Find research fields by label."""
        pass

    @abstractmethod
    def save(self, research_field: ResearchField) -> ResearchField:
        """Save a research field."""
        pass


class JournalRepository(ABC):
    """Repository interface for Journal entities."""

    @abstractmethod
    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find journals by name."""
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
        """Get latest journals with filters."""
        pass


class SearchRepository(ABC):
    """Repository interface for search operations."""

    @abstractmethod
    def semantic_search_statements(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on statements."""
        pass

    @abstractmethod
    def semantic_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on articles."""
        pass

    @abstractmethod
    def keyword_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword search on statements."""
        pass

    @abstractmethod
    def keyword_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform keyword search on articles."""
        pass

    @abstractmethod
    def hybrid_search_statements(
        self, query: str, k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Perform hybrid search on statements."""
        pass

    @abstractmethod
    def hybrid_search_articles(
        self, query: str, k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Perform hybrid search on articles."""
        pass

    @abstractmethod
    def add_statements(self, statements: List[Dict[str, str]]) -> bool:
        """Add statements to search index."""
        pass

    @abstractmethod
    def add_articles(self, articles: List[Dict[str, str]]) -> bool:
        """Add articles to search index."""
        pass

    @abstractmethod
    def delete_indices(self) -> bool:
        """Delete search indices."""
        pass
