from datetime import datetime
import logging
from typing import List, Optional, Tuple
from core.application.interfaces.repositories.search import SearchRepository
from core.application.interfaces.repositories.statement import StatementRepository
from core.domain.entities import Author, Concept, Journal, Article, Statement
from core.domain.exceptions import DatabaseError
from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
    Statement as StatementModel,
    Author as AuthorModel,
)
from django.core.paginator import Paginator
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F, Case, When

from core.infrastructure.repositories.sql_repos_helper import generate_static_id

logger = logging.getLogger(__name__)


class SQLStatementRepository(StatementRepository):
    """PostgreSQL implementation of the Statement repository."""

    def find_all(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Statement], int]:
        """Find all statements with pagination."""
        try:
            queryset = StatementModel.objects.all().order_by("id")
            total = queryset.count()

            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            statements = []
            for statement_model in page_obj:
                statement = self._convert_statement_to_entity(statement_model)
                statements.append(statement)

            return statements, total

        except Exception as e:
            logger.error(f"Error in find_all: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements: {str(e)}")

    def get_count_all(self, research_fields=None) -> any:
        try:
            if not research_fields:
                return StatementModel.objects.count()
            else:
                return (
                    StatementModel.objects.filter(
                        article__research_fields__in=research_fields
                    )
                    .distinct()
                    .count()
                )

        except Exception as e:
            logger.error(f"Error in count all statements: {str(e)}")
            raise DatabaseError(f"Failed to count all statements: {str(e)}")

    def find_paper_with_statement_details(
        self, statement_id: str
    ) -> Optional[Statement]:
        """Find a statement by its ID."""
        # try:
        print(
            "--------------find_paper_with_statement_details-----find_by_id-----------------",
            __file__,
        )
        statement_model = StatementModel.objects.filter(
            statement_id=statement_id
        ).first()

        if statement_model:
            return self._convert_article_to_paper_statement(
                statement_model.article, statement_id
            )

        # if statement_model:
        #     return self._convert_statement_to_entity(statement_model)

        return None

        # except Exception as e:
        #     logger.error(f"Error in find_by_id: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve statement: {str(e)}")

    def find_by_id(self, statement_id: str) -> Optional[Statement]:
        """Find a statement by its ID."""
        # try:
        print(
            "--------------SQLStatementRepository-----find_by_id-----------------",
            __file__,
        )
        statement_model = StatementModel.objects.filter(
            statement_id=statement_id
        ).first()
        # if statement_model:
        #     return self._convert_statement_to_entity(statement_model)

        return statement_model

        # except Exception as e:
        #     logger.error(f"Error in find_by_id: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve statement: {str(e)}")

    def find_by_paper_id(self, paper_id: str) -> List[Statement]:
        """Find statements by paper ID."""
        try:
            statements_queryset = StatementModel.objects.filter(article_id=paper_id)

            statements = []
            for statement_model in statements_queryset:
                statement = self._convert_statement_to_entity(statement_model)
                statements.append(statement)

            return statements

        except Exception as e:
            logger.error(f"Error in find_by_paper_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements by paper ID: {str(e)}")

    def save(self, statement: Statement) -> Statement:
        """Save a statement."""
        try:
            if not statement.id:
                statement.id = generate_static_id(
                    statement.article_id + str(datetime.utcnow())
                )

            # Convert authors to proper format
            author_data = []
            for author in statement.author:
                author_data.append(
                    {
                        "id": author.id,
                        "given_name": author.given_name,
                        "family_name": author.family_name,
                        "label": author.label
                        or f"{author.given_name} {author.family_name}",
                    }
                )

            # Create or update statement
            statement_model, created = StatementModel.objects.update_or_create(
                id=statement.id,
                defaults={
                    "statement_id": statement.statement_id or statement.id,
                    "content": statement.content,
                    "author": author_data,
                    "article_id": statement.article_id,
                    "supports": statement.supports or [],
                    "authors_id": [author.id for author in statement.author],
                    "updated_at": datetime.utcnow(),
                },
            )

            # Set created_at only on creation
            if created:
                statement_model.created_at = datetime.utcnow()
                statement_model.save()

            # Handle author relationships if they exist in database
            author_instances = []
            for author_entity in statement.author:
                author = AuthorModel.objects.filter(id=author_entity.id).first()
                if author:
                    author_instances.append(author)

            if author_instances:
                statement_model.authors.clear()
                statement_model.authors.add(*author_instances)

            return statement

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save statement: {str(e)}")

    def _convert_article_to_paper_statement(
        self, article: ArticleModel, statement_id
    ) -> Article:
        authors = []
        print("--------_convert_article_to_paper_statement-----------", __file__)
        for author in article.authors.all():
            authors.append(
                Author(
                    id=author.id,
                    orcid=author.orcid,
                    given_name=author.given_name,
                    family_name=author.family_name,
                    author_id=author.author_id,
                    name=author.name,
                )
            )
        journal = None
        # if article.journal_conference:
        #     journal = Journal(
        #         id=article.journal_conference.id,
        #         label=article.journal_conference.label,
        #         publisher=article.publisher_id,
        #     )

        concepts = []
        for concept in article.concepts.all():
            concepts.append(Concept(id=concept.concept_id, label=concept.label))

        print("--------------find_by_id----1111111111111--------", __file__)
        return Article(
            id=article.id,
            name=article.name,
            authors=authors,
            abstract=article.description,
            contributions=[],
            statements=article.statements.all(),
            dois=article.reborn_doi,
            date_published=article.date_published,
            entity=None,
            external=None,
            info={},
            timeline={},
            journal=journal,
            publisher=article.publisher,
            # research_fields=research_fields,
            article_id=article.article_id,
            reborn_doi=article.reborn_doi,
            paper_type=article.research_types,
            concepts=concepts,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    def advanced_statement_search(self, query_text, research_field_ids=None):
        print("-----advanced_statement_search------------")
        if not query_text.strip():
            return StatementModel.objects.none()

        search_vector = (
            SearchVector("label", weight="A")
            + SearchVector("content", weight="B")
            + SearchVector("article__name", weight="C")
            + SearchVector("article__abstract", weight="D")
        )

        words = query_text.split()
        if len(words) > 1:
            phrase_query = SearchQuery(" & ".join(words), search_type="raw")
            words_query = SearchQuery(" | ".join(words), search_type="raw")

            search_query = phrase_query | words_query
        else:
            search_query = SearchQuery(query_text)

        queryset = (
            StatementModel.objects.select_related("article")
            .annotate(
                search=search_vector, base_rank=SearchRank(search_vector, search_query)
            )
            .filter(search=search_query)
        )

        if research_field_ids:
            queryset = queryset.filter(
                article__research_fields__research_field_id__in=research_field_ids
            ).distinct()

        queryset = queryset.annotate(final_rank=F("base_rank")).order_by("-final_rank")

        return queryset

    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
    ) -> Tuple[List[Statement], int]:
        print("----------get_latest_statements------", __file__)
        # try:
        if search_query and search_type in ["semantic", "hybrid"]:
            from core.infrastructure.container import Container

            search_repo = Container.resolve(SearchRepository)

            if search_type == "semantic":
                search_results = search_repo.semantic_search_statements(
                    search_query, page_size * 2
                )
                statement_ids = [
                    result.get("statement_id")
                    for result in search_results
                    if result.get("statement_id")
                ]
            else:
                search_results = search_repo.hybrid_search_statements(
                    search_query, page_size * 2
                )
                statement_ids = [
                    result.get("statement_id")
                    for result in search_results
                    if result.get("statement_id")
                ]

            if not statement_ids:
                query = self.advanced_statement_search(search_query, research_fields)
            else:
                preserved_order = Case(
                    *[
                        When(statement_id=id, then=pos)
                        for pos, id in enumerate(statement_ids)
                    ]
                )
                query = StatementModel.objects.filter(
                    statement_id__in=statement_ids
                ).order_by(preserved_order)

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    article__research_fields__research_field_id__in=research_fields
                )
        else:
            if search_query:
                query = self.advanced_statement_search(search_query, research_fields)
            else:
                query = StatementModel.objects.select_related("article").all()

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    article__research_fields__research_field_id__in=research_fields
                )
        if search_type not in ["semantic", "hybrid"]:
            if sort_order == "a-z":
                query = query.order_by("label")
            elif sort_order == "z-a":
                query = query.order_by("-label")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("label")

        total = query.count()
        paginator = Paginator(query, page_size)
        page_obj = paginator.get_page(page)

        statements = []
        for statement_model in page_obj:
            statement = self._convert_statement_to_entity(statement_model)
            statements.append(statement)
        return statements, total

        # except Exception as e:
        #     logger.error(f"Error in get_latest_statements: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve latest statements: {str(e)}")

    def get_semantics_statements(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        """Get statements by IDs from semantic search."""
        try:
            query = StatementModel.objects.filter(id__in=ids).select_related("article")

            # Apply sorting
            if sort_order == "a-z":
                query = query.order_by("article__name")
            elif sort_order == "z-a":
                query = query.order_by("-article__name")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("article__name")

            # Get total count before pagination (limited to 10 as in the original)
            total = min(query.count(), 10)

            # Apply pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            statements = []
            for statement_model in page_obj:
                statement = self._convert_statement_to_entity(statement_model)
                statements.append(statement)

            return statements, total

        except Exception as e:
            logger.error(f"Error in get_semantics_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements by IDs: {str(e)}")

    def _convert_statement_to_entity(
        self, statement_model: StatementModel
    ) -> Statement:
        authors = []
        for author in statement_model.authors.all():
            authors.append(
                Author(
                    id=author.id,
                    author_id=author.author_id,
                    given_name=author.given_name,
                    orcid=author.orcid,
                    family_name=author.family_name,
                    name=author.name,
                )
            )
        if not authors and statement_model.author:
            for author_data in statement_model.author:
                authors.append(
                    Author(
                        id=author_data.get("id", ""),
                        given_name=author_data.get("given_name", ""),
                        orcid=author.orcid,
                        family_name=author_data.get("family_name", ""),
                        name=author_data.get("name", ""),
                    )
                )

        article_authors = []
        for author in statement_model.article.authors.all():
            article_authors.append(
                Author(
                    id=author.id,
                    orcid=author.orcid,
                    given_name=author.given_name,
                    family_name=author.family_name,
                    author_id=author.author_id,
                    name=author.name,
                )
            )
        journal = None
        # if statement_model.article.journal_conference:
        #     journal = Journal(
        #         id=statement_model.article.journal_conference.id,
        #         label=statement_model.article.journal_conference.label,
        #         publisher=statement_model.article.publisher_id,
        #     )

        article_concepts = []
        for concept in statement_model.article.concepts.all():
            article_concepts.append(Concept(id=concept.concept_id, label=concept.label))

        article = {
            "concepts": article_concepts,
            "journal": journal,
            "authors": article_authors,
            "abstract": statement_model.article.description,
            "dois": statement_model.article.reborn_doi,
            "date_published": statement_model.article.date_published,
            "publisher": statement_model.article.publisher,
            "article_id": statement_model.article.article_id,
            "reborn_doi": statement_model.article.reborn_doi,
            "created_at": statement_model.article.created_at,
        }

        return Statement(
            id=statement_model.id,
            label=statement_model.label,
            article=article,
            author=authors,
            article_id=statement_model.article_id,
            article_name=statement_model.article.name,
            date_published=statement_model.article.date_published,
            journal_conference=statement_model.article.publisher.name,
            statement_id=statement_model.statement_id,
            created_at=statement_model.created_at,
            updated_at=statement_model.updated_at,
        )
