from abc import ABC, abstractmethod

class InsightService(ABC):
    """Service interface for auto-complete operations."""

    @abstractmethod
    def get_research_insights(self) -> any:
        """Get authors."""
        pass