from abc import ABC, abstractmethod


class InsightService(ABC):
    @abstractmethod
    def get_research_insights(self) -> any:
        pass