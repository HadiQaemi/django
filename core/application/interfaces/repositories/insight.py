from abc import ABC, abstractmethod
from typing import List, Optional


class InsightRepository(ABC):
    @abstractmethod
    def get_research_insights(self) -> any:
        pass

    @abstractmethod
    def get_per_month_articles_statements(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass

    @abstractmethod
    def get_software_library_with_usage(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass

    @abstractmethod
    def get_data_type_with_usage(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass

    @abstractmethod
    def get_programming_language_with_usage(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass

    @abstractmethod
    def get_concepts_with_usage(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass

    @abstractmethod
    def get_components_with_usage(
        self, research_fields: Optional[List[str]] = None
    ) -> any:
        pass
