
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from core.domain.entities import Concept


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