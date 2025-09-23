
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from core.domain.entities import Article
from core.domain.value_objects import YearRange


class PaperRepository(ABC):
    @abstractmethod
    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Article], int]:
        pass

    @abstractmethod
    def find_by_id(self, paper_id: str) -> Optional[Article]:
        pass

    @abstractmethod
    def search_by_title(self, title: str) -> List[Article]:
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
    ) -> Tuple[List[Article], int]:
        pass

    @abstractmethod
    def save(self, paper: Article) -> Article:
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
        resource_type: str = "loom",

        year_range: Any = None,
        authors: Optional[List[str]] = None,
        scientific_venues: Optional[List[str]] = None,
        concepts: Optional[List[str]] = None,
    ) -> Tuple[List[Article], int]:
        pass

    @abstractmethod
    def delete_database(self) -> bool:
        pass

    @abstractmethod
    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        pass
