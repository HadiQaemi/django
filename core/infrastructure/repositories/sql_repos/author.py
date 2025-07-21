from typing import List, Optional, Tuple
import logging
from sympy import Q
from core.application.interfaces.repositories.author import AuthorRepository
from core.domain.entities import Author
from core.domain.exceptions import DatabaseError
from django.core.paginator import Paginator
from core.infrastructure.models.sql_models import Author as AuthorModel
from core.infrastructure.repositories.sql_repos_helper import generate_static_id

logger = logging.getLogger(__name__)


class SQLAuthorRepository(AuthorRepository):
    """PostgreSQL implementation of the Author repository."""

    def get_authors_by_name(
        self, search_query: str, page: int, page_size: int
    ) -> List[Author]:
        """Find authors by name."""
        print("-------get_authors_by_name-------", __file__)
        # try:
        authors_queryset = AuthorModel.objects.filter(
            label__icontains=search_query
        ).order_by("label")[:5]
        authors = []
        for author_model in authors_queryset:
            author = Author(
                author_id=author_model.author_id,
                orcid=author_model.orcid,
                given_name=author_model.given_name,
                family_name=author_model.family_name,
                label=author_model.label,
            )
            authors.append(author)
        return authors

        # except Exception as e:
        #     logger.error(f"Error in find_by_name: {str(e)}")
        #     raise DatabaseError(f"Failed to find authors: {str(e)}")

    def get_count_all(self) -> any:
        """Find authors by name."""
        print("-------get_count_all-------", __file__)
        try:
            return AuthorModel.objects.count()

        except Exception as e:
            logger.error(f"Error in count all authors: {str(e)}")
            raise DatabaseError(f"Failed to count all authors: {str(e)}")

    def save(self, author: Author) -> Author:
        """Save an author."""
        try:
            if not author.id:
                author.id = generate_static_id(author.given_name + author.family_name)

            # Create or update author
            author_model, created = AuthorModel.objects.update_or_create(
                id=author.id,
                defaults={
                    "given_name": author.given_name,
                    "family_name": author.family_name,
                    "label": author.label
                    or f"{author.given_name} {author.family_name}",
                },
            )

            return author

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save author: {str(e)}")

    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Author], int]:
        """Get latest authors with filters."""
        print("-------------get_latest_authors----------", __file__)
        try:
            query = AuthorModel.objects.all()
            if search_query:
                query = query.filter(
                    Q(label__icontains=search_query)
                    | Q(given_name__icontains=search_query)
                    | Q(family_name__icontains=search_query)
                )

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    articles__research_fields__research_field_id__in=research_fields
                )

            if sort_order == "a-z":
                query = query.order_by("label")
            elif sort_order == "z-a":
                query = query.order_by("-label")
            elif sort_order == "newest":
                query = query.order_by("-id")
            else:
                query = query.order_by("label")

            total = query.count()

            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            authors = []
            for author_model in page_obj:
                author = Author(
                    id=author_model.id,
                    orcid=author_model.orcid,
                    author_id=author_model.author_id,
                    given_name=author_model.given_name,
                    family_name=author_model.family_name,
                    label=author_model.label,
                )
                authors.append(author)

            return authors, total

        except Exception as e:
            logger.error(f"Error in get_latest_authors: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest authors: {str(e)}")
