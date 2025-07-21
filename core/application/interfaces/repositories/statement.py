
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.domain.entities import Statement


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
