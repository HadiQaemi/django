from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.domain.entities import Author


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
