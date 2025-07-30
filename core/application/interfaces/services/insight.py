from abc import ABC, abstractmethod


class InsightService(ABC):
    @abstractmethod
    def get_research_insights(self) -> any:
        pass

    @abstractmethod
    def get_research_components(self, research_field) -> any:
        pass

    @abstractmethod
    def get_research_concepts(self, research_field) -> any:
        pass
