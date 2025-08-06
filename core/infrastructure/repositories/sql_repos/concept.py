import logging
from typing import List, Optional, Tuple
from core.application.interfaces.repositories.concept import ConceptRepository
from core.domain.entities import Concept
from django.core.paginator import Paginator
from core.domain.exceptions import DatabaseError
from core.infrastructure.repositories.sql_repos_helper import generate_static_id
from core.infrastructure.models.sql_models import Concept as ConceptModel

logger = logging.getLogger(__name__)


class SQLConceptRepository(ConceptRepository):
    """PostgreSQL implementation of the Concept repository."""

    def get_keywords_by_label(
        self, search_query: str, page: int, page_size: int
    ) -> List[Concept]:
        """Find concepts by label."""
        print("-------concepts-------", __file__)
        try:
            concepts_queryset = ConceptModel.objects.filter(
                label__icontains=search_query
            ).order_by("label")[:3]
            concepts = []
            for concept_model in concepts_queryset:
                concept = Concept(
                    id=concept_model.id,
                    label=concept_model.label,
                    concept_id=concept_model.concept_id,
                )
                concepts.append(concept)
            return concepts

        except Exception as e:
            logger.error(f"Error in find_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find authors: {str(e)}")

    def get_count_all(self) -> any:
        print("-------get_count_all-------", __file__)
        try:
            return ConceptModel.objects.count()

        except Exception as e:
            logger.error(f"Error in count all research_field: {str(e)}")
            raise DatabaseError(f"Failed to count all research_field: {str(e)}")

    def find_by_label(self, label: str) -> List[Concept]:
        """Find concepts by label."""
        try:
            concepts_queryset = ConceptModel.objects.filter(
                label__icontains=label
            ).order_by("label")[:3]  # Limit to 10 concepts

            concepts = []
            for concept_model in concepts_queryset:
                concept = Concept(
                    id=concept_model.id,
                    label=concept_model.label,
                    identifier=concept_model.identifier,
                )
                concepts.append(concept)

            return concepts

        except Exception as e:
            logger.error(f"Error in find_by_label: {str(e)}")
            raise DatabaseError(f"Failed to find concepts: {str(e)}")

    def save(self, concept: Concept) -> Concept:
        """Save a concept."""
        try:
            if not concept.id:
                concept.id = generate_static_id(concept.label)

            # Create or update concept
            concept_model, created = ConceptModel.objects.update_or_create(
                id=concept.id,
                defaults={"label": concept.label, "identifier": concept.identifier},
            )

            return concept

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save concept: {str(e)}")

    def get_latest_concepts(self, limit: int = 8) -> List[Concept]:
        """Get latest concepts."""
        try:
            concepts_queryset = ConceptModel.objects.all().order_by("-id")[:limit]

            concepts = []
            for concept_model in concepts_queryset:
                concept = Concept(
                    id=concept_model.id,
                    label=concept_model.label,
                    identifier=concept_model.identifier,
                )
                concepts.append(concept)

            return concepts

        except Exception as e:
            logger.error(f"Error in get_latest_concepts: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest concepts: {str(e)}")

    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Concept], int]:
        """Get latest keywords with filters."""
        try:
            query = ConceptModel.objects.all()

            if search_query:
                query = query.filter(label__icontains=search_query)

            if research_fields and len(research_fields) > 0:
                query = query.filter(research_fields_id__overlap=research_fields)

            # Apply sorting
            if sort_order == "a-z":
                query = query.order_by("label")
            elif sort_order == "z-a":
                query = query.order_by("-label")
            elif sort_order == "newest":
                query = query.order_by("-id")
            else:
                query = query.order_by("label")

            # Get total count before pagination
            total = query.count()

            # Apply pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            concepts = []
            for concept_model in page_obj:
                concept = Concept(
                    id=concept_model.id,
                    label=concept_model.label,
                    identifier=concept_model.identifier,
                )
                concepts.append(concept)

            return concepts, total

        except Exception as e:
            logger.error(f"Error in get_latest_keywords: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest keywords: {str(e)}")
