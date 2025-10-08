import logging

from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.services.auto_complete import (
    AutoCompleteService as AutoCompleteServiceInterface,
)

from core.application.dtos.input_dtos import AutoCompleteInputDTO
from core.application.dtos.output_dtos import (
    SearchResultsDTO,
    CommonResponseDTO,
)
from core.domain.exceptions import SearchEngineError

logger = logging.getLogger(__name__)


class AutoCompleteServiceImpl(AutoCompleteServiceInterface):
    def __init__(
        self,
        author_repository: AuthorRepository,
        concept_repository: ConceptRepository,
        research_field_repository: ResearchFieldRepository,
        journal_repository: JournalRepository,
    ):
        self.author_repository = author_repository
        self.concept_repository = concept_repository
        self.research_field_repository = research_field_repository
        self.journal_repository = journal_repository

    def get_authors_by_name(self, search_dto: AutoCompleteInputDTO) -> SearchResultsDTO:
        # cache_key = f"get_authors_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            query = search_dto.query
            page = search_dto.page
            page_size = search_dto.page_size

            authors = self.author_repository.get_authors_by_name(
                search_query=query,
                page=page,
                page_size=page_size,
            )
            # cache.set(cache_key, authors, settings.CACHE_TTL)
            return [{"id": au.author_id, "name": au.name} for au in authors]

        except Exception as e:
            logger.error(f"Error in search authers by name {str(e)}")
            raise SearchEngineError(
                f"Failed to perform search authers by name: {str(e)}"
            )

    def get_academic_publishers_by_name(
        self, search_dto: AutoCompleteInputDTO
    ) -> SearchResultsDTO:
        # cache_key = f"get_authors_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            query = search_dto.query
            page = search_dto.page
            page_size = search_dto.page_size

            academic_publishers = (
                self.journal_repository.get_academic_publishers_by_name(
                    search_query=query,
                    page=page,
                    page_size=page_size,
                )
            )
            # cache.set(cache_key, authors, settings.CACHE_TTL)
            return [
                {"id": ap.journal_conference_id, "name": ap.label}
                for ap in academic_publishers
            ]

        except Exception as e:
            logger.error(f"Error in search academic publishers by name {str(e)}")
            raise SearchEngineError(
                f"Failed to perform search academic publishers by name: {str(e)}"
            )

    def get_keywords_by_label(
        self, search_dto: AutoCompleteInputDTO
    ) -> SearchResultsDTO:
        # cache_key = f"get_authors_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            query = search_dto.query
            page = search_dto.page
            page_size = search_dto.page_size

            keywords = self.concept_repository.get_keywords_by_label(
                search_query=query,
                page=page,
                page_size=page_size,
            )
            # cache.set(cache_key, authors, settings.CACHE_TTL)
            return [{"id": ks.concept_id, "name": ks.label} for ks in keywords]

        except Exception as e:
            logger.error(f"Error in search keywords by name {str(e)}")
            raise SearchEngineError(
                f"Failed to perform search keywords by name: {str(e)}"
            )

    def get_research_fields_by_name(
        self, search_dto: AutoCompleteInputDTO
    ) -> CommonResponseDTO:
        # cache_key = f"get_authors_{search_dto.query}_{search_dto.search_type}_{search_dto.sort_order}_{search_dto.page}_{search_dto.page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            query = search_dto.query
            page = search_dto.page
            page_size = search_dto.page_size

            research_fields = (
                self.research_field_repository.get_research_fields_by_name(
                    search_query=query,
                    page=page,
                    page_size=page_size,
                )
            )
            # cache.set(cache_key, authors, settings.CACHE_TTL)
            return [
                {"id": ks.research_field_id, "name": ks.label} for ks in research_fields
            ]

        except Exception as e:
            logger.error(f"Error in search research fields by name {str(e)}")
            raise SearchEngineError(
                f"Failed to perform search research fields by name: {str(e)}"
            )
