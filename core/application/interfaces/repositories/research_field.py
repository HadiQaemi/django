from abc import ABC, abstractmethod
from typing import List

from core.domain.entities import ResearchField


class ResearchFieldRepository(ABC):
    @abstractmethod
    def get_research_fields_by_name(self, label: str) -> List[ResearchField]:
        pass

    @abstractmethod
    def save(self, research_field: ResearchField) -> ResearchField:
        pass
