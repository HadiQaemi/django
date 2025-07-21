from abc import ABC, abstractmethod


class InsightRepository(ABC):
    @abstractmethod
    def get_research_insights(self) -> any:
        pass
