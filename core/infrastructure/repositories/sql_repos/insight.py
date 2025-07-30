from core.application.interfaces.repositories.insight import InsightRepository
from core.domain.exceptions import DatabaseError
from django.db.models import Count
from core.infrastructure.models.sql_models import (
    Software as SoftwareModel,
    SoftwareLibrary as SoftwareLibraryModel,
)
import logging

logger = logging.getLogger(__name__)


class SQLInsightRepository(InsightRepository):
    """PostgreSQL implementation of the research insights repository."""

    def get_research_components(self) -> any:
        return True

    def get_research_insights(self) -> any:
        """Find insights."""
        try:
            models_by_label = SoftwareModel.objects.values("label").annotate(
                model_count=Count("id")
            )
            libraries_by_label = SoftwareLibraryModel.objects.values(
                "part_of__label"
            ).annotate(library_count=Count("id"))
            return [
                {
                    "models_by_label": models_by_label,
                    "libraries_by_label": libraries_by_label,
                }
            ]

        except Exception as e:
            logger.error(f"Error in get_research_insights: {str(e)}")
            raise DatabaseError(f"Failed to find research insights: {str(e)}")
