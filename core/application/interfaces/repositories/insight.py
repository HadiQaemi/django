from abc import ABC, abstractmethod


class InsightRepository(ABC):
    @abstractmethod
    def get_research_insights(self) -> any:
        pass

    @abstractmethod
    def get_research_components(self) -> any:
        pass

    @abstractmethod
    def get_research_concepts(self) -> any:
        pass
