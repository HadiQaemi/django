import logging
from typing import Any, Dict, List, Optional, Tuple
from core.application.interfaces.repositories.journal import JournalRepository
from core.domain.entities import Journal
from core.domain.exceptions import DatabaseError
from core.infrastructure.models.sql_models import (
    JournalConference as JournalConferenceModel,
    Periodical as PeriodicalModel,
)
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


class SQLJournalRepository(JournalRepository):
    def get_academic_publishers_by_name(
        self, search_query: str, page: int, page_size: int
    ) -> List[Journal]:
        try:
            journals_queryset = PeriodicalModel.objects.filter(
                name__icontains=search_query
            ).order_by("name")[:5]
            journals = []
            for journal_model in journals_queryset:
                journal = Journal(
                    id=journal_model.id,
                    label=journal_model.name,
                    journal_conference_id=journal_model.periodical_id,
                    publisher=journal_model.publisher.name,
                )
                journals.append(journal)
            return journals

        except Exception as e:
            logger.error(f"Error in get_academic_publishers_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find academic publishers: {str(e)}")

    def get_count_all(self, research_fields=None) -> any:
        try:
            if not research_fields:
                return PeriodicalModel.objects.count()
            else:
                return (
                    PeriodicalModel.objects.filter(research_fields__in=research_fields)
                    .distinct()
                    .count()
                )

        except Exception as e:
            logger.error(f"Error in count all journals: {str(e)}")
            raise DatabaseError(f"Failed to count all journals: {str(e)}")

    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        try:
            query = PeriodicalModel.objects.all()

            if search_query:
                query = query.filter(label__icontains=search_query)

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    articles__research_fields__research_field_id__in=research_fields
                )

            if sort_order == "a-z":
                query = query.order_by("name")
            elif sort_order == "z-a":
                query = query.order_by("-name")
            elif sort_order == "newest":
                query = query.order_by("-id")
            else:
                query = query.order_by("name")

            total = query.count()

            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)
            periodicals = []
            for periodical in page_obj:
                periodical_dict = {
                    "id": periodical.periodical_id,
                    "journal_conference_id": periodical.periodical_id,
                    "label": periodical.name,
                    "publisher": periodical.publisher.name,
                    "url": periodical.publisher.url,
                }
                periodicals.append(periodical_dict)
            return periodicals, total

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest journals: {str(e)}")
