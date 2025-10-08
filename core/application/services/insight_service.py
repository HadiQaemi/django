import logging

from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.repositories.statement import StatementRepository
from core.application.interfaces.repositories.insight import InsightRepository
from core.application.interfaces.services.insight import (
    InsightService as InsightServiceInterface,
)

from core.domain.exceptions import SearchEngineError


from core.infrastructure.models.sql_models import (
    ResearchField as ResearchFieldModel,
)

logger = logging.getLogger(__name__)


class InsightServiceImpl(InsightServiceInterface):
    def __init__(
        self,
        author_repository: AuthorRepository,
        concept_repository: ConceptRepository,
        research_field_repository: ResearchFieldRepository,
        journal_repository: JournalRepository,
        paper_repository: PaperRepository,
        statement_repository: StatementRepository,
        insight_repository: InsightRepository,
    ):
        self.author_repository = author_repository
        self.concept_repository = concept_repository
        self.research_field_repository = research_field_repository
        self.journal_repository = journal_repository
        self.paper_repository = paper_repository
        self.statement_repository = statement_repository
        self.insight_repository = insight_repository

    def get_research_insights(self, research_fields=None) -> any:

        try:
            concepts_with_usage = self.insight_repository.get_concepts_with_usage(
                research_fields
            )
            components_with_usage = self.insight_repository.get_components_with_usage(
                research_fields
            )
            data_types_with_usage = self.insight_repository.get_data_type_with_usage(
                research_fields
            )
            programming_languages_with_usage = (
                self.insight_repository.get_programming_language_with_usage(
                    research_fields
                )
            )
            packages_with_usage = (
                self.insight_repository.get_software_library_with_usage(research_fields)
            )
            articles_statements_per_month = (
                self.insight_repository.get_per_month_articles_statements(
                    research_fields
                )
            )
            research_fields = ResearchFieldModel.objects.filter(
                research_field_id__in=research_fields
            )
            return {
                "statistics": {
                    "Articles": self.paper_repository.get_count_all(research_fields),
                    "Scientific statements": self.statement_repository.get_count_all(
                        research_fields
                    ),
                    "Journals": self.journal_repository.get_count_all(research_fields),
                    "Authors": self.author_repository.get_count_all(research_fields),
                },
                "articles_statements_per_month": articles_statements_per_month,
                "programming_languages_with_usage": programming_languages_with_usage,
                "packages_with_usage": packages_with_usage,
                "data_types_with_usage": data_types_with_usage,
                "concepts_with_usage": concepts_with_usage,
                "components_with_usage": components_with_usage,
            }

        except Exception as e:
            logger.error(f"Error in research components {str(e)}")
            raise SearchEngineError(f"Failed to perform research components: {str(e)}")
