from abc import ABC, abstractmethod
from core.application.dtos.input_dtos import AutoCompleteInputDTO, SearchInputDTO
from core.application.dtos.output_dtos import CommonResponseDTO, SearchResultsDTO


class AutoCompleteService(ABC):

    @abstractmethod
    def get_authors_by_name(self, search_dto: AutoCompleteInputDTO) -> SearchResultsDTO:
        pass

    @abstractmethod
    def get_academic_publishers_by_name(
        self, search_dto: AutoCompleteInputDTO
    ) -> SearchResultsDTO:
        pass

    @abstractmethod
    def get_research_fields_by_name(
        self, search_dto: SearchInputDTO
    ) -> CommonResponseDTO:
        pass

    @abstractmethod
    def get_keywords_by_label(self, search_dto: SearchInputDTO) -> CommonResponseDTO:
        pass
