from typing import List
import logging
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.domain.entities import ResearchField
from core.domain.exceptions import DatabaseError
from core.infrastructure.repositories.sql_repos_helper import generate_static_id
from core.infrastructure.models.sql_models import ResearchField as ResearchFieldModel

logger = logging.getLogger(__name__)


class SQLResearchFieldRepository(ResearchFieldRepository):
    def get_research_fields_by_name(
        self, search_query: str, page: int, page_size: int
    ) -> List[ResearchField]:
        try:
            research_fields_queryset = ResearchFieldModel.objects.filter(
                label__icontains=search_query
            ).order_by("label")[:5]
            research_fields = []
            for research_model in research_fields_queryset:
                research_field = ResearchField(
                    id=research_model.id,
                    label=research_model.label,
                    research_field_id=research_model.research_field_id,
                )
                research_fields.append(research_field)
            return research_fields

        except Exception as e:
            logger.error(f"Error in get_research_fields_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find research fields by name: {str(e)}")

    def get_count_all(self) -> any:
        try:
            return ResearchFieldModel.objects.count()

        except Exception as e:
            logger.error(f"Error in count all research_field: {str(e)}")
            raise DatabaseError(f"Failed to count all research_field: {str(e)}")

    def find_by_label(self, label: str) -> List[ResearchField]:
        try:
            rf_queryset = ResearchFieldModel.objects.filter(
                label__icontains=label
            ).order_by("label")[:5]

            research_fields = []
            for rf_model in rf_queryset:
                research_field = ResearchField(
                    id=rf_model.id,
                    label=rf_model.label,
                    research_field_id=rf_model.research_field_id,
                    related_identifier=rf_model.related_identifier,
                )
                research_fields.append(research_field)

            return research_fields

        except Exception as e:
            logger.error(f"Error in find_by_label: {str(e)}")
            raise DatabaseError(f"Failed to find research fields: {str(e)}")

    def save(self, research_field: ResearchField) -> ResearchField:
        try:
            if not research_field.id:
                research_field.id = generate_static_id(research_field.label)

            rf_model, created = ResearchFieldModel.objects.update_or_create(
                id=research_field.id,
                defaults={
                    "label": research_field.label,
                    "research_field_id": generate_static_id(research_field.label),
                },
            )

            return research_field

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save research field: {str(e)}")
