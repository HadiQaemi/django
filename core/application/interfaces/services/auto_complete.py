from abc import ABC, abstractmethod
from core.application.dtos.input_dtos import AutoCompleteInputDTO, SearchInputDTO
from core.application.dtos.output_dtos import CommonResponseDTO, SearchResultsDTO


class AutoCompleteService(ABC):
    """Service interface for auto-complete operations."""

    @abstractmethod
    def get_authors_by_name(self, search_dto: AutoCompleteInputDTO) -> SearchResultsDTO:
        """Get authors."""
        pass

    @abstractmethod
    def get_academic_publishers_by_name(
        self, search_dto: AutoCompleteInputDTO
    ) -> SearchResultsDTO:
        """Get academic publishers."""
        pass

    @abstractmethod
    def get_research_fields_by_name(
        self, search_dto: SearchInputDTO
    ) -> CommonResponseDTO:
        """Get research fields."""
        pass

    @abstractmethod
    def get_keywords_by_label(self, search_dto: SearchInputDTO) -> CommonResponseDTO:
        """Get keywords."""
        pass
