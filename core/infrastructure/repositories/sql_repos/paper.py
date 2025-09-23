import re
import sys
from typing import Any, Dict, List, Optional, Tuple
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.search import SearchRepository
from core.domain.entities import Author, Concept, Journal, Article, ResearchField
from core.infrastructure.clients.type_registry_client import TypeRegistryClient
from core.infrastructure.repositories.sql_repos_helper import (
    fetch_reborn_doi,
    generate_static_id,
    is_orcid_url,
    process_source_code_content_flexible,
)
from core.infrastructure.scrapers.node_extractor import NodeExtractor
from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
    DigitalObjectAuthor as DigitalObjectAuthorModel,
    ScholarlyArticle as ScholarlyArticleModel,
    ScholarlyArticleAuthor as ScholarlyArticleAuthorModel,
    Dataset as DatasetModel,
    DatasetAuthor as DatasetAuthorModel,
    # DigitalObject as DigitalObjectModel,
    Statement as StatementModel,
    DataType as DataTypeModel,
    Implement as ImplementModel,
    HasPart as HasPartModel,
    DescriptiveStatistics as DescriptiveStatisticsModel,
    AlgorithmEvaluation as AlgorithmEvaluationModel,
    GroupComparison as GroupComparisonModel,
    RegressionAnalysis as RegressionAnalysisModel,
    DataPreprocessing as DataPreprocessingModel,
    FactorAnalysis as FactorAnalysisModel,
    ClassDiscovery as ClassDiscoveryModel,
    CorrelationAnalysis as CorrelationAnalysisModel,
    Figure as FigureModel,
    MartixSize as MartixSizeModel,
    DataItemComponent as DataItemComponentModel,
    DataItem as DataItemModel,
    SharedType as SharedTypeModel,
    Software as SoftwareModel,
    SoftwareLibrary as SoftwareLibraryModel,
    SoftwareMethod as SoftwareMethodModel,
    MultilevelAnalysis as MultilevelAnalysisModel,
    ClassPrediction as ClassPredictionModel,
    FactorAnalysis as FactorAnalysisModel,
    Author as AuthorModel,
    Property as PropertyModel,
    Operation as OperationModel,
    Component as ComponentModel,
    Constraint as ConstraintModel,
    ObjectOfInterest as ObjectOfInterestModel,
    Unit as UnitModel,
    Matrix as MatrixModel,
    Concept as ConceptModel,
    ResearchField as ResearchFieldModel,
    JournalConference as JournalConferenceModel,
    Publisher as PublisherModel,
    Organization as OrganizationModel,
    Periodical as PeriodicalModel,
    PublicationIssue as PublicationIssueModel,
    CreativeWork as CreativeWorkModel,
    Contribution as ContributionModel,
)
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, F, Case, When
from core.domain.exceptions import DatabaseError
from django.core.paginator import Paginator
from datetime import datetime
import dateutil.parser
import logging

logger = logging.getLogger(__name__)


class SQLPaperRepository(PaperRepository):
    """PostgreSQL implementation of the Paper repository."""

    def __init__(self, type_registry_client: TypeRegistryClient):
        """Initialize the repository."""
        self.type_registry_client = type_registry_client
        self.scraper = NodeExtractor()

    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Article], int]:
        """Find all papers with pagination."""
        # try:
        print("---------find_all-----queryset----------", __file__)
        queryset = (
            ArticleModel.objects.all()
            .only("name", "date_published")
            .prefetch_related("authors", "journal_conference")
        )
        total = queryset.count()
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        papers = []
        for article in page_obj:
            paper = self._convert_article_to_paper(article)
            papers.append(paper)
        return papers, total
        # except Exception as e:
        #     logger.error(f"Error in find_all: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve papers: {str(e)}")

    def get_count_all(self, research_fields=None) -> any:
        try:
            if not research_fields:
                return ArticleModel.objects.count()
            else:
                return (
                    ArticleModel.objects.filter(research_fields__in=research_fields)
                    .distinct()
                    .count()
                )

        except Exception as e:
            logger.error(f"Error in count all articles: {str(e)}")
            raise DatabaseError(f"Failed to count all articles: {str(e)}")

    def find_by_id(self, paper_id: str) -> Optional[Article]:
        """Find a paper by its ID."""
        print("---------------find_by_id------------", __file__)
        try:
            article = ArticleModel.objects.filter(article_id=paper_id).first()
            if article:
                return self._convert_article_to_paper(article)

            return None

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve paper: {str(e)}")

    def search_by_title(self, title: str) -> List[Article]:
        """Search papers by title."""
        try:
            articles = ArticleModel.objects.filter(name__icontains=title).order_by(
                "name"
            )

            papers = []
            for article in articles:
                paper = self._convert_article_to_paper(article)
                papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f"Error in search_by_title: {str(e)}")
            raise DatabaseError(f"Failed to search papers: {str(e)}")

    def query_papers(
        self,
        title: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        author_ids: Optional[List[str]] = None,
        scientific_venue_ids: Optional[List[str]] = None,
        concept_ids: Optional[List[str]] = None,
        research_field_ids: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Article], int]:
        """Query papers with filters."""
        print("--------query_papers-------", __file__)
        try:
            from django.contrib.postgres.search import SearchQuery, SearchRank
            from django.db.models import Q, F
            from datetime import datetime

            query = ArticleModel.objects.all()

            if title:
                search_query = SearchQuery(title)
                query = query.filter(search_vector=search_query)
                query = query.annotate(
                    search_rank=SearchRank("search_vector", search_query)
                )
                query = query.filter(
                    Q(search_vector=search_query) | Q(name__icontains=title)
                )

            if author_ids and len(author_ids) > 0:
                query = query.filter(authors__author_id__in=author_ids)

            if scientific_venue_ids and len(scientific_venue_ids) > 0:
                query = query.filter(
                    journal_conference__journal_conference_id__in=scientific_venue_ids
                )

            if concept_ids and len(concept_ids) > 0:
                query = query.filter(concepts__concept_id__in=concept_ids)

            if start_year and end_year:
                start_date = datetime(int(start_year), 1, 1)
                end_date = datetime(int(end_year), 12, 31, 23, 59, 59)
                query = query.filter(date_published__range=[start_date, end_date])
            elif start_year:
                start_date = datetime(int(start_year), 1, 1)
                query = query.filter(date_published__gte=start_date)
            elif end_year:
                end_date = datetime(int(end_year), 12, 31, 23, 59, 59)
                query = query.filter(date_published__lte=end_date)

            if research_field_ids and len(research_field_ids) > 0:
                query = query.filter(
                    research_fields__research_field_id__in=research_field_ids
                )

            query = query.distinct()

            query = query.select_related("journal_conference").prefetch_related(
                "authors", "concepts", "research_fields"
            )
            if title:
                query = query.order_by("-search_rank", "-date_published", "name")
            else:
                query = query.order_by("-date_published", "name")
            total = query.count()
            paginator = Paginator(query, page_size)
            if page < 1:
                page = 1
            elif page > paginator.num_pages and paginator.num_pages > 0:
                page = paginator.num_pages

            page_obj = paginator.get_page(page)

            papers = []
            for article in page_obj:
                paper = self._convert_article_to_paper(article)
                papers.append(paper)
            return papers, total

        except Exception as e:
            logger.error(f"Error in query_papers: {str(e)}")
            raise DatabaseError(f"Failed to query papers: {str(e)}")

    def save(self, paper: Article) -> Article:
        """Save a paper."""
        try:
            # Check if paper already exists
            if not paper.id:
                paper.id = generate_static_id(paper.title)

            article, created = ArticleModel.objects.update_or_create(
                id=paper.id,
                defaults={
                    "article_id": paper.article_id or generate_static_id(paper.title),
                    "name": paper.title,
                    "abstract": paper.abstract,
                    "date_published": paper.date_published,
                    "publisher": paper.publisher or {},
                    "journal": paper.journal.__dict__ if paper.journal else {},
                    "conference": paper.conference.__dict__ if paper.conference else {},
                    "identifier": paper.dois,
                    "paper_type": paper.paper_type,
                    "reborn_doi": paper.reborn_doi,
                    "research_field": [rf.__dict__ for rf in paper.research_fields]
                    if paper.research_fields
                    else [],
                    "research_fields_id": paper.research_fields_id or [],
                    "author_ids": [author.id for author in paper.author]
                    if paper.author
                    else [],
                    "updated_at": datetime.utcnow(),
                },
            )

            # Set created_at only on creation
            if created:
                article.created_at = datetime.utcnow()
                article.save()

            # Handle relationships
            if paper.author:
                # Create/update authors and link to article
                author_instances = []
                for author_entity in paper.author:
                    author, _ = AuthorModel.objects.update_or_create(
                        id=author_entity.id,
                        defaults={
                            "given_name": author_entity.given_name,
                            "family_name": author_entity.family_name,
                            "label": author_entity.label,
                            "author_id": generate_static_id(author_entity.label)
                            or f"{author_entity.given_name} {author_entity.family_name}",
                        },
                    )
                    author_instances.append(author)

                # Clear and re-add authors
                article.authors.clear()
                article.authors.add(*author_instances)

            if paper.research_fields:
                # Create/update research fields and link to article
                rf_instances = []
                for rf_entity in paper.research_fields:
                    rf, _ = ResearchFieldModel.objects.update_or_create(
                        id=rf_entity.id, defaults={"label": rf_entity.label}
                    )
                    rf_instances.append(rf)

                # Clear and re-add research fields
                article.research_fields.clear()
                article.research_fields.add(*rf_instances)

            if paper.concepts:
                # Create/update concepts and link to article
                concept_instances = []
                for concept_entity in paper.concepts:
                    concept, _ = ConceptModel.objects.update_or_create(
                        id=concept_entity.id,
                        concept_id=generate_static_id(concept_entity.label),
                        defaults={
                            "label": concept_entity.label,
                            "identifier": concept_entity.identifier,
                            "concept_id": generate_static_id(concept_entity.label),
                        },
                    )
                    concept_instances.append(concept)

                # Clear and re-add concepts
                article.concepts.clear()
                article.concepts.add(*concept_instances)

            return paper

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save paper: {str(e)}")

    def advanced_article_search(self, query_text, resource_type=None):
        from django.db.models.functions import Coalesce, Greatest
        from django.db.models import FloatField

        if not query_text or not query_text.strip():
            return ArticleModel.objects.none()

        words = query_text.split()
        if len(words) > 1:
            phrase_q = SearchQuery(" & ".join(words), search_type="raw")
            words_q = SearchQuery(" | ".join(words), search_type="raw")
            search_q = phrase_q | words_q
        else:
            search_q = SearchQuery(query_text)

        qs = ArticleModel.objects

        qs = qs.annotate(
            a_rank=SearchRank(F("search_vector"), search_q),  # Article tsvector
            sa_rank=SearchRank(
                F("related_scholarly_articles__search_vector"), search_q
            ),  # ScholarlyArticle tsvector
            ds_rank=SearchRank(
                F("related_datasets__search_vector"), search_q
            ),  # Dataset tsvector
        )

        if resource_type == "loom":
            match_filter = Q(search_vector=search_q)
        elif resource_type == "article":
            match_filter = Q(related_scholarly_articles__search_vector=search_q)
        elif resource_type == "dataset":
            match_filter = Q(related_datasets__search_vector=search_q)
        else:
            match_filter = (
                Q(search_vector=search_q)
                | Q(related_scholarly_articles__search_vector=search_q)
                | Q(related_datasets__search_vector=search_q)
            )

        qs = qs.filter(match_filter)
        qs = qs.distinct()
        qs = qs.annotate(
            final_rank=Greatest(
                Coalesce(F("a_rank"), 0.0),
                Coalesce(F("sa_rank"), 0.0),
                Coalesce(F("ds_rank"), 0.0),
                output_field=FloatField(),
            )
        ).order_by("-final_rank", "-a_rank", F("date_published").desc(nulls_last=True))

        return qs

    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
        resource_type: str = "loom",
        year_range: Any = None,
        authors: Optional[List[str]] = None,
        scientific_venues: Optional[List[str]] = None,
        concepts: Optional[List[str]] = None,
    ) -> Tuple[List[Article], int]:
        """Get latest articles with filters."""
        print("-------------get_latest_articles---------------", __file__)

        # try:
        if search_query and search_type in ["semantic", "hybrid"]:
            from core.infrastructure.container import Container

            search_repo = Container.resolve(SearchRepository)
            if search_type == "semantic":
                search_results = search_repo.semantic_search_articles(
                    search_query, page_size * 2
                )
                article_ids = [
                    result.get("article_id")
                    for result in search_results
                    if result.get("article_id")
                ]
            else:
                search_results = search_repo.hybrid_search_articles(
                    search_query, page_size * 2
                )
                article_ids = [
                    result.get("article_id")
                    for result in search_results
                    if result.get("article_id")
                ]
            if not article_ids:
                query = self.advanced_article_search(search_query, resource_type)
            else:
                preserved_order = Case(
                    *[
                        When(article_id=id, then=pos)
                        for pos, id in enumerate(article_ids)
                    ]
                )
                query = ArticleModel.objects.filter(
                    article_id__in=article_ids
                ).order_by(preserved_order)

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    research_fields__research_field_id__in=research_fields
                )
        else:
            if search_query:
                query = self.advanced_article_search(search_query, resource_type)
            else:
                query = ArticleModel.objects.all()

            if research_fields and len(research_fields) > 0:
                query = query.filter(
                    research_fields__research_field_id__in=research_fields
                )
            # # print(resource_type)
            # if authors:
            #     query = query.filter(authors__author_id__in=authors).distinct()

            if authors:
                if resource_type == "loom":
                    query = query.filter(authors__author_id__in=authors)
                elif resource_type == "article":
                    query = query.filter(
                        related_scholarly_articles__authors__author_id__in=authors
                    )
                elif resource_type == "dataset":
                    query = query.filter(
                        related_datasets__authors__author_id__in=authors
                    )
                else:  # "all" -> match authors on ANY of the three
                    query = query.filter(
                        Q(authors__author_id__in=authors) |
                        Q(related_scholarly_articles__authors__author_id__in=authors) |
                        Q(related_datasets__authors__author_id__in=authors)
                    )

                query = query.distinct()

            if concepts:
                query = query.filter(concepts__concept_id__in=concepts).distinct()

            if scientific_venues:
                query = query.filter(
                    related_scholarly_articles__is_part_of__is_part_of__periodical_id__in=scientific_venues
                ).distinct()

        if search_type not in ["semantic", "hybrid"]:
            if sort_order == "a-z":
                query = query.order_by("name")
            elif sort_order == "z-a":
                query = query.order_by("-name")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("name")

        total = query.count()

        paginator = Paginator(query, page_size)
        page_obj = paginator.get_page(page)
        papers = []
        for article in page_obj:
            paper = self._convert_article_to_paper(article)
            papers.append(paper)

        return papers, total

        # except Exception as e:
        #     logger.error(f"Error in get_latest_articles: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve latest articles: {str(e)}")

    def get_semantics_articles(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Article], int]:
        """Get articles by IDs from semantic search."""
        try:
            query = ArticleModel.objects.filter(id__in=ids)

            # Apply sorting
            if sort_order == "a-z":
                query = query.order_by("name")
            elif sort_order == "z-a":
                query = query.order_by("-name")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("name")

            # Get total count before pagination (limited to 10 as in the original)
            total = min(query.count(), 10)

            # Apply pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            papers = []
            for article in page_obj:
                paper = self._convert_article_to_paper(article)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in get_semantics_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve articles by IDs: {str(e)}")

    def delete_database(self) -> bool:
        """Delete the database."""
        try:
            # Delete all data in the tables
            ContributionModel.objects.all().delete()
            StatementModel.objects.all().delete()
            ImplementModel.objects.all().delete()
            DataTypeModel.objects.all().delete()
            HasPartModel.objects.all().delete()
            DescriptiveStatisticsModel.objects.all().delete()
            AlgorithmEvaluationModel.objects.all().delete()
            GroupComparisonModel.objects.all().delete()
            RegressionAnalysisModel.objects.all().delete()
            DataPreprocessingModel.objects.all().delete()
            FactorAnalysisModel.objects.all().delete()
            ClassDiscoveryModel.objects.all().delete()
            CorrelationAnalysisModel.objects.all().delete()
            FigureModel.objects.all().delete()
            MartixSizeModel.objects.all().delete()
            DataItemComponentModel.objects.all().delete()
            DataItemModel.objects.all().delete()
            SharedTypeModel.objects.all().delete()
            SoftwareModel.objects.all().delete()
            SoftwareLibraryModel.objects.all().delete()
            SoftwareMethodModel.objects.all().delete()
            MultilevelAnalysisModel.objects.all().delete()
            ClassPredictionModel.objects.all().delete()
            FactorAnalysisModel.objects.all().delete()
            ArticleModel.objects.all().delete()
            AuthorModel.objects.all().delete()
            ConceptModel.objects.all().delete()
            ResearchFieldModel.objects.all().delete()
            JournalConferenceModel.objects.all().delete()

            return True

        except Exception as e:
            logger.error(f"Error in delete_database: {str(e)}")
            return False

    def get_property_info(self, info, property):
        try:
            _type = info["@type"]
            if f"{_type}#{property}" in info:
                return info[f"{_type}#{property}"]
            elif f"{_type}#{property}".replace("doi:", "doi:21.T11969/") in info:
                return info[f"{_type}#{property}".replace("doi:", "doi:21.T11969/")]

        except Exception as e:
            print(f"{str(e)}")

    def read_data(self, paper_data):
        graph_data = paper_data.get("@graph", [])
        data = {}
        data["Dataset"] = [
            item for item in graph_data if "Dataset" in item.get("@type", [])
        ]

        data["json_files"] = [
            item
            for item in graph_data
            if item.get("encodingFormat", "") == "application/ld+json"
            and "File" in item.get("@type", [])
        ]
        data["LinguisticStatement"] = {
            item["@id"]: item
            for item in graph_data
            if "LinguisticStatement" in item.get("@type", [])
        }
        data["statements"] = {
            item["@id"]: item
            for item in graph_data
            if "Statement" in item.get("@type", [])
        }

        ###############
        data["organizations"] = [
            item for item in graph_data if "Organization" in item.get("@type", [])
        ]
        organizations_id = {}
        for organization in data["organizations"]:
            organization_obj, created = OrganizationModel.objects.update_or_create(
                organization_id=organization.get("@id", ""),
                defaults={
                    "name": organization.get("name", ""),
                    "url": organization.get("url", ""),
                },
            )
            organizations_id[organization.get("@id", "")] = organization_obj

        ###############
        data["persons"] = [
            item for item in graph_data if "Person" in item.get("@type", [])
        ]
        persons_id = {}
        for person in data["persons"]:
            person_obj, created = AuthorModel.objects.update_or_create(
                author_id=generate_static_id(person.get("name", "")),
                defaults={
                    "family_name": person.get("familyName", ""),
                    "given_name": person.get("givenName", ""),
                    "orcid": person.get("@id", "")
                    if is_orcid_url(person.get("@id", ""))
                    else "",
                    "name": person.get("name", ""),
                    "affiliation": organizations_id[person["affiliation"]["@id"]],
                },
            )
            persons_id[person.get("@id", "")] = person_obj

        ###############
        data["periodicals"] = [
            item for item in graph_data if "Periodical" in item.get("@type", [])
        ]
        periodicals_id = {}
        for periodical in data["periodicals"]:
            periodical_obj, created = PeriodicalModel.objects.update_or_create(
                periodical_id=periodical.get("@id", ""),
                defaults={
                    "name": periodical.get("name", ""),
                    "publisher": organizations_id[periodical["publisher"]["@id"]],
                },
            )
            periodicals_id[periodical.get("@id", "")] = periodical_obj
        ###############
        data["publication_issues"] = [
            item for item in graph_data if "PublicationIssue" in item.get("@type", [])
        ]
        publication_issues_id = {}
        for publication_issue in data["publication_issues"]:
            key = generate_static_id(publication_issue.get("@id", "") or "")
            publication_issue_obj, created = (
                PublicationIssueModel.objects.update_or_create(
                    publication_issue_id=key,
                    defaults={
                        "date_published": publication_issue.get("datePublished", ""),
                        "is_part_of": periodicals_id[
                            publication_issue["isPartOf"]["@id"]
                        ],
                    },
                )
            )
            publication_issues_id[key] = publication_issue_obj.pk
        ###############
        data["creativeWorks"] = [
            item for item in graph_data if "CreativeWork" in item.get("@type", [])
        ]
        creative_works_id = {}
        for creative_work in data["creativeWorks"]:
            creative_work_obj, created = CreativeWorkModel.objects.update_or_create(
                creative_work_id=creative_work.get("@id", ""),
                defaults={
                    "name": creative_work.get("name", ""),
                    "description": creative_work.get("description", ""),
                    "identifier": creative_work.get("identifier", ""),
                },
            )
            creative_works_id[creative_work.get("@id", "")] = creative_work_obj

        ###############
        data["concepts"] = [
            item for item in graph_data if "skos:Concept" in item.get("@type", [])
        ]
        concepts_id = {}
        for concept in data["concepts"]:
            concept_obj, created = ConceptModel.objects.get_or_create(
                concept_id=generate_static_id(concept.get("rdfs:label", "")),
                label=concept.get("rdfs:label", ""),
                defaults={
                    "json": concept,
                    "definition": concept.get("skos:definition", ""),
                    "see_also": concept.get("rdfs:seeAlso", ""),
                    "string_match": concept.get("stringMatch", "")
                    if len(concept.get("stringMatch", "").strip())
                    else [],
                },
            )
            concepts_id[concept.get("@id", "")] = concept_obj

        ###############
        units_id = {}
        data["units"] = [item for item in graph_data if "Unit" in item.get("@type", [])]
        for unit in data["units"]:
            unit_obj, created = UnitModel.objects.get_or_create(
                type=unit.get("@type", ""),
                unit_id=generate_static_id(unit.get("rdfs:label", "")),
                exact_match=unit.get("skos:exactMatch", "")
                if len(unit.get("skos:exactMatch", "")) > 0
                else [],
                close_match=unit.get("skos:closeMatch", "")
                if len(unit.get("skos:closeMatch", "")) > 0
                else [],
                label=unit.get("rdfs:label", ""),
                defaults={
                    "json": unit,
                },
            )
            units_id[unit.get("@id", "")] = unit_obj

        ###############
        object_of_interests_id = {}
        data["object_of_interests"] = [
            item for item in graph_data if "ObjectOfInterest" in item.get("@type", [])
        ]
        for object_of_interest in data["object_of_interests"]:
            object_of_interest_obj, created = (
                ObjectOfInterestModel.objects.get_or_create(
                    type=object_of_interest.get("@type", ""),
                    exact_match=object_of_interest.get("skos:exactMatch", "")
                    if len(object_of_interest.get("skos:exactMatch", "")) > 0
                    else [],
                    close_match=object_of_interest.get("skos:closeMatch", "")
                    if len(object_of_interest.get("skos:closeMatch", "")) > 0
                    else [],
                    label=object_of_interest.get("rdfs:label", "")
                    if len(object_of_interest.get("rdfs:label", "")) > 0
                    else [],
                    defaults={
                        "json": object_of_interest,
                    },
                )
            )
            object_of_interests_id[object_of_interest.get("@id", "")] = (
                object_of_interest_obj
            )

        ###############
        matrices_id = {}
        data["matrices"] = [
            item for item in graph_data if "Matrix" in item.get("@type", [])
        ]
        for matrix in data["matrices"]:
            matrix_obj, created = MatrixModel.objects.get_or_create(
                exact_match=matrix.get("skos:exactMatch", "")
                if len(matrix.get("skos:exactMatch", "")) > 0
                else [],
                close_match=matrix.get("skos:closeMatch", "")
                if len(matrix.get("skos:closeMatch", "")) > 0
                else [],
                label=matrix.get("rdfs:label", "")
                if len(matrix.get("rdfs:label", "")) > 0
                else [],
                defaults={
                    "json": matrix,
                    "_id": matrix.get("@id", ""),
                },
            )
            matrices_id[matrix.get("@id", "")] = matrix_obj.id

        ###############
        data["properties"] = [
            item for item in graph_data if "Property" in item.get("@type", [])
        ]
        properties_id = {}
        for property in data["properties"]:
            property_obj, created = PropertyModel.objects.get_or_create(
                exact_match=property.get("skos:exactMatch", "")
                if len(property.get("skos:exactMatch", "")) > 0
                else [],
                close_match=property.get("skos:closeMatch", "")
                if len(property.get("skos:closeMatch", "")) > 0
                else [],
                label=property.get("rdfs:label", "")
                if len(property.get("rdfs:label", "")) > 0
                else [],
                defaults={
                    "json": property,
                },
            )
            properties_id[property.get("@id", "")] = property_obj.id

        ###############
        data["statements"] = {
            item["@id"]: item
            for item in graph_data
            if "Statement" in item.get("@type", [])
        }

        ###############
        data["constraints"] = [
            item for item in graph_data if "Constraint" in item.get("@type", [])
        ]
        constraints_id = {}
        for constraint in data["constraints"]:
            constraint_obj, created = ConstraintModel.objects.get_or_create(
                exact_match=constraint.get("skos:exactMatch", "")
                if len(constraint.get("skos:exactMatch", "")) > 0
                else [],
                close_match=constraint.get("skos:closeMatch", "")
                if len(constraint.get("skos:closeMatch", "")) > 0
                else [],
                label=constraint.get("rdfs:label", "")
                if len(constraint.get("rdfs:label", "")) > 0
                else [],
                defaults={
                    "json": constraint,
                    "_id": constraint.get("@id", ""),
                },
            )
            constraints_id[constraint.get("@id", "")] = constraint_obj.id

        ###############
        operations_id = {}
        data["operations"] = [
            item for item in graph_data if "Operation" in item.get("@type", [])
        ]
        for operation in data["operations"]:
            operation_obj, created = OperationModel.objects.get_or_create(
                exact_match=operation.get("skos:exactMatch", "")
                if len(operation.get("skos:exactMatch", "")) > 0
                else [],
                close_match=operation.get("skos:closeMatch", "")
                if len(operation.get("skos:closeMatch", "")) > 0
                else [],
                label=operation.get("rdfs:label", "")
                if len(operation.get("rdfs:label", "")) > 0
                else [],
                defaults={
                    "json": operation,
                    "_id": operation.get("@id", ""),
                },
            )
            operations_id[operation.get("@id", "")] = operation_obj.id

        ###############
        types = ["Component", "Variable", "Measure"]
        items = []
        components_id = {}
        for _type in types:
            components = [
                item for item in graph_data if "Component" in item.get("@type", [])
            ]
            for component in components:
                component_obj, created = ComponentModel.objects.get_or_create(
                    type=component.get("@type", ""),
                    label=component.get("rdfs:label", ""),
                    string_match=component.get("stringMatch", "")
                    if len(component.get("stringMatch", "")) > 0
                    else [],
                    exact_match=component.get("skos:exactMatch", "")
                    if len(component.get("skos:exactMatch", "")) > 0
                    else [],
                    close_match=component.get("skos:closeMatch", "")
                    if len(component.get("skos:closeMatch", "")) > 0
                    else [],
                    defaults={
                        "json": component,
                        "_id": component.get("@id", ""),
                    },
                )
                components_id[component.get("@id", "")] = component_obj
                items.append(component_obj)

                if component.get("operation", None) is not None:
                    component_obj.operations.add(
                        operations_id[component.get("operation", None)["@id"]]
                    )

                if component.get("matrix", None) is not None:
                    component_obj.matrices.add(
                        matrices_id[component.get("matrix", None)["@id"]]
                    )

                if component.get("objectOfInterest", None) is not None:
                    component_obj.object_of_interests.add(
                        object_of_interests_id[
                            component.get("objectOfInterest", None)["@id"]
                        ]
                    )

                if component.get("property", None) is not None:
                    component_obj.properties.add(
                        properties_id[component.get("property", None)["@id"]]
                    )

                if component.get("qudt:unit", None) is not None:
                    component_obj.units.set(
                        [units_id[component.get("qudt:unit", None)["@id"]]]
                    )

        ###############
        digital_object = [
            item
            for item in graph_data
            if "Dataset" in item.get("@type", []) and item.get("@id", []) == "./"
        ][0]
        research_fields = []
        for item in digital_object["about"]:
            rf, created = ResearchFieldModel.objects.get_or_create(
                label=item, research_field_id=generate_static_id(item)
            )
            research_fields.append(rf.id)
        ###############
        article_data_items = [
            item
            for item in graph_data
            if (
                "ScholarlyArticle" in item.get("@type")
                or ("Dataset" in item.get("@type", []) and item.get("@id", []) != "./")
            )
        ]
        source_types = []
        reborn_doi = ""
        link_targets = {}
        scholarly_articles = []
        datasets = []
        sources = {}
        for idx, article_data in enumerate(article_data_items):
            if "ScholarlyArticle" in article_data.get("@type"):
                scholarly_article, created = (
                    ScholarlyArticleModel.objects.update_or_create(
                        scholarly_article_id=article_data.get("@id", ""),
                        defaults={
                            "scholarly_article_id": article_data.get("@id", ""),
                            "name": article_data.get("name", ""),
                            "abstract": article_data.get("abstract", ""),
                            "is_part_of": publication_issue_obj,
                            "json": article_data,
                        },
                    )
                )
                if not created:
                    ScholarlyArticleAuthorModel.objects.filter(
                        article=scholarly_article
                    ).delete()

                for idx, author in enumerate(article_data.get("author", "")):
                    scholarly_article.authors.add(
                        persons_id[author["@id"]], through_defaults={"order": idx + 1}
                    )

                sources[article_data.get("@id", "")] = {
                    "scholarly_article": scholarly_article,
                    "source_type": "scholarly_article",
                }
                reborn_doi = (
                    fetch_reborn_doi(article_data.get("@id", ""))
                    if len(fetch_reborn_doi(article_data.get("@id", "")))
                    else ""
                )
                source_types.append("scholarly_article")
                scholarly_articles.append(scholarly_article)
            else:
                article_data = [
                    item
                    for item in graph_data
                    if "Dataset" in item.get("@type", [])
                    and item.get("@id", []) != "./"
                ][0]
                publisher = article_data.get("publisher", "")

                date_published_raw = article_data.get("datePublished", "")
                date_published = None
                if isinstance(date_published_raw, (int, float)):  # timestamp case
                    date_published = datetime.fromtimestamp(date_published_raw)
                elif isinstance(date_published_raw, str) and date_published_raw.strip():
                    date_published = dateutil.parser.parse(date_published_raw)
                dataset, created = DatasetModel.objects.update_or_create(
                    dataset_id=article_data.get("@id", ""),
                    defaults={
                        "dataset_id": article_data.get("@id", ""),
                        "name": article_data.get("name", ""),
                        "description": article_data.get("description", ""),
                        "date_published": date_published,
                        "identifier": article_data.get("identifier", ""),
                        "publisher": organizations_id[publisher.get("@id", "")],
                        "json": article_data,
                    },
                )
                if not created:
                    DatasetAuthorModel.objects.filter(dataset=dataset).delete()

                for idx, author in enumerate(article_data.get("creator", "")):
                    dataset.authors.add(
                        persons_id[author["@id"]], through_defaults={"order": idx + 1}
                    )

                sources[article_data.get("@id", "")] = {
                    "dataset": dataset,
                    "source_type": "dataset",
                }
                reborn_doi = (
                    fetch_reborn_doi(article_data.get("@id", ""))
                    if len(fetch_reborn_doi(article_data.get("@id", "")))
                    else ""
                )
                source_types.append("dataset")
                datasets.append(dataset)
        link_targets = {
            "scholarly_articles": scholarly_articles,
            "datasets": datasets,
        }
        return (
            data,
            reborn_doi,
            link_targets,
            digital_object,
            research_fields,
            source_types,
            creative_works_id,
            organizations_id,
            components_id,
            persons_id,
            concepts_id,
        )

    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        scraper = NodeExtractor()
        (
            data,
            reborn_doi,
            link_targets,
            digital_object,
            research_fields,
            source_types,
            creative_works_id,
            organizations_id,
            components_id,
            authors_id,
            concepts_id,
        ) = self.read_data(paper_data)

        article_id = generate_static_id(digital_object.get("name", ""))
        dt = datetime.strptime(digital_object["datePublished"], "%Y-%m-%dT%H:%M:%S%z")
        article, created = ArticleModel.objects.update_or_create(
            article_id=article_id,
            defaults={
                "name": digital_object["name"],
                "description": digital_object["description"],
                "date_published": dt,
                "license": creative_works_id[digital_object["license"]["@id"]],
                "publisher": organizations_id[digital_object["publisher"]["@id"]],
                "status": digital_object["status"],
                ##
                "reborn_doi": reborn_doi,
                "article_id": article_id,
                "json": digital_object,
                "research_types": source_types,
            },
        )
        if len(link_targets["scholarly_articles"]):
            article.related_scholarly_articles.set(link_targets["scholarly_articles"])
        else:
            article.related_datasets.set(link_targets["datasets"])

        if not created:
            DigitalObjectAuthorModel.objects.filter(article=article).delete()

        for idx, author in enumerate(digital_object["author"]):
            article.authors.add(
                authors_id[author["@id"]], through_defaults={"order": idx + 1}
            )
        filename, content_file, mime_type = self.scraper.get_file_content_and_type(
            json_files["ro-crate-metadata.json"]
        )
        article.ro_crate.save(filename, content_file, save=True)
        article.research_fields.set(research_fields)

        for idx, concept in enumerate(concepts_id):
            article.concepts.add(concepts_id[concept])

        for statement_index, statement_item in enumerate(data["json_files"]):
            statement_content = scraper.load_json_from_url(
                json_files[statement_item.get("name", "")]
            )

            if not statement_content:
                continue
            statement_properties = {}
            statement_properties["components"] = statement_item.get("components", "")
            statement_properties["json_files"] = json_files[
                statement_item.get("name", "")
            ]

            for support in statement_item.get("supports", ""):
                # notation = data["LinguisticStatement"][
                #     data["statements"][support["@id"]]["notation"]["@id"]
                # ]
                notation = data["statements"][support["@id"]]
                statement_properties["author"] = digital_object["author"]
                statement_properties["label"] = notation["rdfs:label"]
                statement_properties["concept"] = notation["concepts"]
            statement, created = StatementModel.objects.update_or_create(
                _id=statement_item["@id"],
                defaults={
                    "label": statement_properties["label"],
                    "order": statement_index + 1,
                    "statement_id": generate_static_id(statement_properties["label"]),
                    "name": json_files[statement_item.get("name", "")],
                    "json": statement_item,
                    "content": statement_content,
                    "article_id": article.id,
                    # "version": statement_item["version"],
                    "version": 1,
                    "encodingFormat": statement_item["encodingFormat"],
                },
            )
            filename, content_file, mime_type = self.scraper.get_file_content_and_type(
                json_files[statement_item.get("name", "")]
            )
            statement.json_ld.save(filename, content_file, save=True)
            if not created:
                statement.implement_statements.all().delete()
                statement.has_part_statements.all().delete()

                for dtype in statement.data_type_statement.all():
                    for method in dtype.executes.all():
                        for library in method.part_of.all():
                            software = library.part_of
                            library.delete()
                            if software and not software.part_of_software.exists():
                                software.delete()
                        method.delete()
                    dtype.executes.clear()
                    for data_item in dtype.has_inputs.all():
                        if data_item is not None:
                            data_item.has_expression.clear()
                            data_item.has_part.clear()
                            # if data_item.has_characteristic is not None:
                            #     data_item.has_characteristic.delete()

                            data_item.delete()

                    dtype.has_inputs.clear()

                    for data_item in dtype.has_outputs.all():
                        if data_item is not None:
                            data_item.has_expression.clear()
                            data_item.has_part.clear()

                            # if data_item.has_characteristic is not None:
                            #     data_item.has_characteristic.delete()

                            data_item.delete()

                    dtype.has_outputs.clear()

                    if isinstance(dtype, MultilevelAnalysisModel):
                        dtype.targets.clear()
                        dtype.level.clear()
                    elif isinstance(dtype, MultilevelAnalysisModel):
                        dtype.targets.clear()
                    elif isinstance(dtype, MultilevelAnalysisModel):
                        dtype.targets.clear()
                    elif isinstance(dtype, MultilevelAnalysisModel):
                        dtype.targets.clear()
                    elif isinstance(dtype, MultilevelAnalysisModel):
                        if dtype.evaluate_id:
                            dtype.evaluate.delete()
                        if dtype.evaluates_for_id:
                            dtype.evaluates_for.delete()
                    dtype.delete()

            statement_components = []
            for component in statement_item.get("components", ""):
                statement_components.append(components_id[component["@id"]])
            if statement_components:
                statement.components.set(statement_components)

            statement_concepts = []
            for concept in statement_properties["concept"]:
                statement_concepts.append(concepts_id[concept["@id"]])
            if statement_concepts:
                statement.concepts.set(statement_concepts)

            statement_authors = []
            for author in statement_properties["author"]:
                statement_authors.append(authors_id[author["@id"]])
            if statement_authors:
                statement.authors.set(statement_authors)

            type_info, _info = self.type_registry_client.get_type_info(
                statement_content["@type"].replace("doi:", "")
            )
            # print(f"Line: {sys._getframe(0).f_lineno}", statement_content["@type"])
            # print(
            #     f"Line: {sys._getframe(0).f_lineno}",
            #     f"{statement_content['@type']}#label",
            # )
            # print('----------type_info["property"]--------------')
            # print(statement_content)

            for property in _info["property"]:
                p = property
                if property.replace("21.T11969/", "") in statement_content:
                    p = property.replace("21.T11969/", "")

                if p in statement_content:
                    if p.endswith("#is_implemented_by"):
                        implement, created = ImplementModel.objects.update_or_create(
                            article_id=article_id,
                            statement_id=statement.id,
                            defaults={
                                "url": statement_content[p],
                            },
                        )
                        filename, content_file, mime_type = (
                            self.scraper.get_file_content_and_type(statement_content[p])
                        )

                        if mime_type:
                            processed_content_file = (
                                process_source_code_content_flexible(
                                    content_file,
                                    filename,
                                    article_id=article_id,
                                )
                            )

                            implement.source_code.save(
                                filename, processed_content_file, save=True
                            )
                    elif p.endswith("#has_part"):
                        # print("#has_part")
                        has_parts = statement_content[p]
                        if isinstance(statement_content[p], dict):
                            has_parts = [statement_content[p]]
                        software_method_items = []
                        for statement_content_item in has_parts:
                            _type_info, _info = self.type_registry_client.get_type_info(
                                statement_content_item["@type"].replace("doi:", "")
                            )
                            label_items = [
                                item for item in _info["property"] if "#label" in item
                            ]
                            HasPartModel.objects.update_or_create(
                                label=statement_content_item[label_items[0]]
                                if label_items[0] in statement_content_item
                                else "",
                                statement=statement,
                                defaults={
                                    "label": statement_content_item[label_items[0]]
                                    if label_items[0] in statement_content_item
                                    else "",
                                    "statement": statement,
                                    "type": _info["name"],
                                    "schema_type": _type_info,
                                    "description": _info["description"],
                                },
                            )
                            label = ""
                            see_also = ""
                            target_items = []
                            has_output_items = []
                            has_input_items = []
                            software_method_item = None
                            for _property in _type_info.property:
                                _p = _property
                                if (
                                    _property.replace("21.T11969/", "")
                                    in statement_content_item
                                ):
                                    _p = _property.replace("21.T11969/", "")
                                if _p not in statement_content_item:
                                    continue
                                if _p.endswith("#has_output"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#has_output",
                                        _p,
                                    )
                                    has_outputs = statement_content_item[_p]
                                    if not isinstance(has_outputs, list):
                                        has_outputs = [has_outputs]
                                    for has_output in has_outputs:
                                        has_output_source_table = (
                                            self.get_property_info(
                                                has_output, "source_table"
                                            )
                                        )
                                        has_output_label = self.get_property_info(
                                            has_output, "label"
                                        )
                                        has_output_source_url = self.get_property_info(
                                            has_output, "source_url"
                                        )
                                        has_output_comment = self.get_property_info(
                                            has_output, "comment"
                                        )
                                        if isinstance(has_output_comment, str):
                                            has_output_comment = [has_output_comment]

                                        has_output_has_parts = []
                                        has_output_has_part = self.get_property_info(
                                            has_output, "has_part"
                                        )
                                        if has_output_has_part:
                                            if not isinstance(
                                                has_output_has_part, (dict, list)
                                            ):
                                                has_output_has_part = [
                                                    has_output_has_part
                                                ]
                                            for item in has_output_has_part:
                                                item_label = self.get_property_info(
                                                    item, "label"
                                                )
                                                item_see_also = self.get_property_info(
                                                    item, "see_also"
                                                )
                                                has_part, created = (
                                                    DataItemComponentModel.objects.update_or_create(
                                                        label=item_label,
                                                        see_also=item_see_also,
                                                        defaults={
                                                            "label": item_label,
                                                            "see_also": item_see_also,
                                                        },
                                                    )
                                                )
                                                has_output_has_parts.append(has_part)

                                        has_characteristic = None
                                        has_output_has_characteristic = (
                                            self.get_property_info(
                                                has_output, "has_characteristic"
                                            )
                                        )
                                        if has_output_has_characteristic:
                                            has_expression_number_of_rows = (
                                                self.get_property_info(
                                                    has_output_has_characteristic,
                                                    "number_of_rows",
                                                )
                                            )
                                            has_expression_number_of_columns = (
                                                self.get_property_info(
                                                    has_output_has_characteristic,
                                                    "number_of_columns",
                                                )
                                            )
                                            has_characteristic, created = (
                                                MartixSizeModel.objects.update_or_create(
                                                    number_rows=has_expression_number_of_rows,
                                                    number_columns=has_expression_number_of_columns,
                                                    defaults={
                                                        "number_columns": has_expression_number_of_columns,
                                                        "number_rows": has_expression_number_of_rows,
                                                    },
                                                )
                                            )

                                        has_expressions = []
                                        has_output_has_expression = (
                                            self.get_property_info(
                                                has_output, "has_expression"
                                            )
                                        )
                                        if has_output_has_expression:
                                            has_expression_label = (
                                                self.get_property_info(
                                                    has_output_has_expression, "label"
                                                )
                                            )
                                            has_expression_source_url = (
                                                self.get_property_info(
                                                    has_output_has_expression,
                                                    "source_url",
                                                )
                                            )
                                            filename, content_file, mime_type = (
                                                self.scraper.get_file_content_and_type(
                                                    has_expression_source_url
                                                )
                                            )

                                            figure, created = (
                                                FigureModel.objects.update_or_create(
                                                    source_url=has_expression_source_url,
                                                    label=has_expression_label,
                                                    defaults={
                                                        "label": has_expression_label,
                                                        "source_url": has_expression_source_url,
                                                        "article_id": article_id,
                                                    },
                                                )
                                            )
                                            figure.source_image.save(
                                                filename, content_file, save=True
                                            )
                                            has_expressions.append(figure.id)
                                        data_item, created = (
                                            DataItemModel.objects.update_or_create(
                                                label=has_output_label,
                                                source_url=has_output_source_url,
                                                source_table=has_output_source_table,
                                                comment=has_output_comment,
                                                has_characteristic=has_characteristic,
                                                defaults={
                                                    "label": has_output_label,
                                                    "source_url": has_output_source_url,
                                                    "source_table": has_output_source_table,
                                                    "comment": has_output_comment,
                                                    "has_characteristic": has_characteristic,
                                                    "article_id": article_id,
                                                },
                                            )
                                        )
                                        if has_output_source_url:
                                            filename, content_file, mime_type = (
                                                self.scraper.get_file_content_and_type(
                                                    has_output_source_url
                                                )
                                            )
                                            if mime_type:
                                                data_item.source_file.save(
                                                    filename, content_file, save=True
                                                )
                                        if has_expressions:
                                            data_item.has_expression.set(
                                                has_expressions
                                            )
                                        if has_output_has_parts:
                                            data_item.has_part.set(has_output_has_parts)

                                        has_output_items.append(data_item)
                                elif _p.endswith("#has_input"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#has_input",
                                    #     _p,
                                    # )
                                    has_inputs = statement_content_item[_p]
                                    if not isinstance(has_inputs, list):
                                        has_inputs = [has_inputs]

                                    for has_input in has_inputs:
                                        has_input_source_table = self.get_property_info(
                                            has_input, "source_table"
                                        )
                                        has_input_label = self.get_property_info(
                                            has_input, "label"
                                        )
                                        has_input_source_url = self.get_property_info(
                                            has_input, "source_url"
                                        )

                                        has_input_comment = self.get_property_info(
                                            has_input, "comment"
                                        )
                                        if isinstance(has_input_comment, str):
                                            has_input_comment = [has_input_comment]

                                        has_input_has_parts = []
                                        has_input_has_part = self.get_property_info(
                                            has_input, "has_part"
                                        )

                                        if has_input_has_part:
                                            if not isinstance(
                                                has_input_has_part, (dict, list)
                                            ):
                                                has_input_has_part = [
                                                    has_input_has_part
                                                ]
                                            for item in has_input_has_part:
                                                label_item = self.get_property_info(
                                                    item, "label"
                                                )
                                                label_see_also = self.get_property_info(
                                                    item, "see_also"
                                                )
                                                has_part, created = (
                                                    DataItemComponentModel.objects.update_or_create(
                                                        label=label_item,
                                                        see_also=label_see_also,
                                                        defaults={
                                                            "label": label_item,
                                                            "see_also": label_see_also,
                                                        },
                                                    )
                                                )
                                                has_input_has_parts.append(has_part)

                                        has_characteristic = None
                                        has_input_has_characteristic = (
                                            self.get_property_info(
                                                has_input, "has_characteristic"
                                            )
                                        )

                                        if has_input_has_characteristic:
                                            has_expression_number_of_rows = (
                                                self.get_property_info(
                                                    has_input_has_characteristic,
                                                    "number_of_rows",
                                                )
                                            )
                                            has_expression_number_of_columns = (
                                                self.get_property_info(
                                                    has_input_has_characteristic,
                                                    "number_of_columns",
                                                )
                                            )

                                            has_characteristic, created = (
                                                MartixSizeModel.objects.update_or_create(
                                                    number_rows=has_expression_number_of_rows,
                                                    number_columns=has_expression_number_of_columns,
                                                    defaults={
                                                        "number_columns": has_expression_number_of_columns,
                                                        "number_rows": has_expression_number_of_rows,
                                                    },
                                                )
                                            )

                                        has_expressions = []
                                        has_input_has_expression = (
                                            self.get_property_info(
                                                has_input,
                                                "has_expression",
                                            )
                                        )
                                        if has_input_has_expression:
                                            has_expression_label = (
                                                self.get_property_info(
                                                    has_input_has_expression,
                                                    "label",
                                                )
                                            )
                                            has_expression_source_url = (
                                                self.get_property_info(
                                                    has_input_has_expression,
                                                    "source_url",
                                                )
                                            )
                                            figure, created = (
                                                FigureModel.objects.update_or_create(
                                                    source_url=has_expression_source_url,
                                                    label=has_expression_label,
                                                    defaults={
                                                        "label": has_expression_label,
                                                        "source_url": has_expression_source_url,
                                                        "article_id": article_id,
                                                    },
                                                )
                                            )
                                            has_expressions.append(figure.id)
                                        data_item, created = (
                                            DataItemModel.objects.update_or_create(
                                                label=has_input_label,
                                                source_url=has_input_source_url,
                                                source_table=has_input_source_table,
                                                comment=has_input_comment,
                                                has_characteristic=has_characteristic,
                                                defaults={
                                                    "label": has_input_label,
                                                    "source_url": has_input_source_url,
                                                    "source_table": has_input_source_table,
                                                    "comment": has_input_comment,
                                                    "has_characteristic": has_characteristic,
                                                    "article_id": article_id,
                                                },
                                            )
                                        )
                                        if has_input_source_url:
                                            filename, content_file, mime_type = (
                                                self.scraper.get_file_content_and_type(
                                                    has_input_source_url
                                                )
                                            )
                                            if mime_type:
                                                data_item.source_file.save(
                                                    filename, content_file, save=True
                                                )
                                        if has_expressions:
                                            data_item.has_expression.set(
                                                has_expressions
                                            )
                                        if has_input_has_parts:
                                            data_item.has_part.set(has_input_has_parts)

                                        has_input_items.append(data_item)
                                elif _p.endswith("#has_part"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#has_part",
                                        _p,
                                    )
                                elif _p.endswith("#evaluates_for"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#evaluates_for",
                                    #     _p,
                                    # )
                                    evaluates_for = statement_content_item[_p]
                                    evaluates_for_see_also = []
                                    evaluates_for_see_also.append(
                                        self.get_property_info(
                                            evaluates_for,
                                            "see_also",
                                        )
                                    )
                                    evaluates_for_label = self.get_property_info(
                                        evaluates_for,
                                        "label",
                                    )
                                    evaluates_for_item, created = (
                                        SharedTypeModel.objects.update_or_create(
                                            see_also=evaluates_for_see_also,
                                            label=evaluates_for_label,
                                            type="evaluates_for",
                                            defaults={
                                                "label": evaluates_for_label,
                                                "see_also": evaluates_for_see_also,
                                                "type": "evaluates_for",
                                            },
                                        )
                                    )
                                elif _p.endswith("#evaluates"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#evaluates",
                                    #     _p,
                                    # )
                                    evaluate = statement_content_item[_p]
                                    evaluate_see_also = []
                                    evaluate_see_also.append(
                                        self.get_property_info(
                                            evaluate,
                                            "see_also",
                                        )
                                    )
                                    evaluate_label = self.get_property_info(
                                        evaluate,
                                        "label",
                                    )
                                    evaluate_item, created = (
                                        SharedTypeModel.objects.update_or_create(
                                            see_also=evaluate_see_also,
                                            label=evaluate_label,
                                            type="evaluates",
                                            defaults={
                                                "label": evaluate_label,
                                                "see_also": evaluate_see_also,
                                                "type": "evaluates",
                                            },
                                        )
                                    )
                                elif _p.endswith("#executes"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "Done #executes",
                                    #     _p,
                                    # )
                                    software_methods = statement_content_item[_p]
                                    software_method_items = []
                                    if not isinstance(software_methods, (list)):
                                        software_methods = [software_methods]
                                    for software_method in software_methods:
                                        software_libraries = self.get_property_info(
                                            software_method,
                                            "part_of",
                                        )
                                        software_libraries_label = (
                                            self.get_property_info(
                                                software_libraries,
                                                "label",
                                            )
                                        )
                                        software_libraries_version_info = (
                                            self.get_property_info(
                                                software_libraries,
                                                "version_info",
                                            )
                                        )
                                        software_libraries_has_support_url = (
                                            self.get_property_info(
                                                software_libraries,
                                                "has_support_url",
                                            )
                                        )

                                        if isinstance(
                                            software_libraries_has_support_url, str
                                        ):
                                            software_libraries_has_support_url = [
                                                software_libraries_has_support_url
                                            ]

                                        softwares = self.get_property_info(
                                            software_libraries,
                                            "part_of",
                                        )
                                        softwares_has_support_url = (
                                            self.get_property_info(
                                                softwares,
                                                "has_support_url",
                                            )
                                        )
                                        softwares_version_info = self.get_property_info(
                                            softwares,
                                            "version_info",
                                        )
                                        softwares_label = self.get_property_info(
                                            softwares,
                                            "label",
                                        )

                                        software_item = SoftwareModel.objects.create(
                                            has_support_url=softwares_has_support_url,
                                            version_info=softwares_version_info,
                                            label=softwares_label,
                                        )
                                        software_libraries_item = SoftwareLibraryModel.objects.create(
                                            has_support_url=software_libraries_has_support_url,
                                            version_info=software_libraries_version_info,
                                            label=software_libraries_label,
                                            part_of=software_item,
                                        )

                                        software_method_label = self.get_property_info(
                                            software_method,
                                            "label",
                                        )
                                        software_method_is_implemented_by = (
                                            self.get_property_info(
                                                software_method,
                                                "is_implemented_by",
                                            )
                                        )
                                        if isinstance(
                                            software_method_is_implemented_by, str
                                        ):
                                            software_method_is_implemented_by = [
                                                software_method_is_implemented_by
                                            ]
                                        software_method_has_support_url = (
                                            self.get_property_info(
                                                software_method,
                                                "has_support_url",
                                            )
                                        )

                                        if isinstance(
                                            software_method_has_support_url, str
                                        ):
                                            software_method_has_support_url = [
                                                software_method_has_support_url
                                            ]
                                        software_method_item = SoftwareMethodModel.objects.create(
                                            has_support_url=software_method_has_support_url,
                                            is_implemented_by=software_method_is_implemented_by,
                                            label=software_method_label,
                                        )
                                        software_method_item.part_of.add(
                                            software_libraries_item
                                        )
                                        software_method_items.append(
                                            software_method_item.id
                                        )
                                elif _p.endswith("#targets"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "Done #targets",
                                    #     _p,
                                    # )
                                    targets = statement_content_item[_p]
                                    if not isinstance(targets, list):
                                        targets = [targets]
                                    for target in targets:
                                        target_see_also = []
                                        target_see_also.append(
                                            self.get_property_info(
                                                target,
                                                "see_also",
                                            )
                                        )
                                        target_label = self.get_property_info(
                                            target,
                                            "label",
                                        )

                                        target_item, created = (
                                            SharedTypeModel.objects.update_or_create(
                                                see_also=target_see_also,
                                                label=target_label,
                                                type="targets",
                                                defaults={
                                                    "label": target_label,
                                                    "see_also": target_see_also,
                                                    "type": "targets",
                                                },
                                            )
                                        )
                                        target_items.append(target_item.id)
                                elif _p.endswith("#label"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#label",
                                    #     _p,
                                    # )
                                    label = statement_content_item[_p]
                                elif _p.endswith("#level"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#level",
                                    #     _p,
                                    # )
                                    levels = statement_content_item[_p]
                                    if not isinstance(levels, list):
                                        levels = [levels]
                                    level_items = []
                                    for level in levels:
                                        # print('------------level["@type"]-----------')
                                        # print(levels)
                                        # print(level)
                                        level_see_also = []
                                        level_label = ""
                                        level_see_also.append(
                                            self.get_property_info(
                                                level,
                                                "see_also",
                                            )
                                        )
                                        level_label = self.get_property_info(
                                            level,
                                            "label",
                                        )

                                        level_item, created = (
                                            SharedTypeModel.objects.update_or_create(
                                                see_also=level_see_also,
                                                label=level_label,
                                                type="levels",
                                                defaults={
                                                    "label": level_label,
                                                    "see_also": level_see_also,
                                                    "type": "levels",
                                                },
                                            )
                                        )
                                        level_items.append(level_item)
                                elif _p.endswith("#see_also"):
                                    # print(
                                    #     f"Line: {sys._getframe(0).f_lineno}",
                                    #     "#see_also",
                                    #     _p,
                                    # )
                                    if _p in statement_content_item:
                                        see_also = statement_content_item[_p]
                                else:
                                    print(f"Line: {sys._getframe(0).f_lineno}", _p)

                                # if _p.endswith("#is_implemented_by"):
                                #     implement, created = (
                                #         ImplementModel.objects.update_or_create(
                                #             url=statement_content_item,
                                #             statement_id=statement.id,
                                #             defaults={
                                #                 "url": statement_content_item,
                                #                 "statement_id": statement.id,
                                #             },
                                #         )
                                #     )
                            # print("_type_info: ", _type_info)

                            # print(_type_info.name)
                            # print(software_method_items)
                            if _type_info.name == "Multilevel analysis":
                                MultilevelAnalysis, created = (
                                    MultilevelAnalysisModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "MultilevelAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_items:
                                    MultilevelAnalysis.targets.set(target_items)
                                if software_method_items:
                                    MultilevelAnalysis.executes.set(
                                        software_method_items
                                    )
                                if level_items:
                                    MultilevelAnalysis.level.set(level_items)
                                if has_output_items:
                                    MultilevelAnalysis.has_outputs.set(has_output_items)
                                if has_input_items:
                                    MultilevelAnalysis.has_inputs.set(has_input_items)
                            elif _type_info.name == "Class prediction":
                                ClassPrediction, created = (
                                    ClassPredictionModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "ClassPrediction",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_items:
                                    ClassPrediction.targets.set(target_items)
                                if software_method_items:
                                    ClassPrediction.executes.set(software_method_items)
                                if has_output_items:
                                    ClassPrediction.has_outputs.set(has_output_items)
                                if has_input_items:
                                    ClassPrediction.has_inputs.set(has_input_items)
                            elif _type_info.name == "Factor analysis":
                                FactorAnalysis, created = (
                                    FactorAnalysisModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "FactorAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if has_output_items:
                                    FactorAnalysis.has_outputs.set(has_output_items)
                                if software_method_items:
                                    FactorAnalysis.executes.set(software_method_items)
                                if has_input_items:
                                    FactorAnalysis.has_inputs.set(has_input_items)
                            elif _type_info.name == "Data preprocessing":
                                DataPreprocessing, created = (
                                    DataPreprocessingModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "DataPreprocessing",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if has_output_items:
                                    DataPreprocessing.has_outputs.set(has_output_items)
                                if software_method_items:
                                    DataPreprocessing.executes.set(
                                        software_method_items
                                    )
                                if has_input_items:
                                    DataPreprocessing.has_inputs.set(has_input_items)
                            elif _type_info.name == "Class discovery":
                                ClassDiscovery, created = (
                                    ClassDiscoveryModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "ClassDiscovery",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if has_output_items:
                                    ClassDiscovery.has_outputs.set(has_output_items)
                                if software_method_items:
                                    ClassDiscovery.executes.set(software_method_items)
                                if has_input_items:
                                    ClassDiscovery.has_inputs.set(has_input_items)
                            elif _type_info.name == "Correlation analysis":
                                CorrelationAnalysis, created = (
                                    CorrelationAnalysisModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "CorrelationAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if has_output_items:
                                    CorrelationAnalysis.has_outputs.set(
                                        has_output_items
                                    )
                                if software_method_items:
                                    CorrelationAnalysis.executes.set(
                                        software_method_items
                                    )
                                if has_input_items:
                                    CorrelationAnalysis.has_inputs.set(has_input_items)
                            elif _type_info.name == "Group comparison":
                                GroupComparison, created = (
                                    GroupComparisonModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "GroupComparison",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_items:
                                    GroupComparison.targets.set(target_items)
                                if software_method_items:
                                    GroupComparison.executes.set(software_method_items)
                                if has_output_items:
                                    GroupComparison.has_outputs.set(has_output_items)
                                if has_input_items:
                                    GroupComparison.has_inputs.set(has_input_items)
                            elif _type_info.name == "Regression analysis":
                                RegressionAnalysis, created = (
                                    RegressionAnalysisModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "RegressionAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_items:
                                    RegressionAnalysis.targets.set(target_items)
                                if software_method_items:
                                    RegressionAnalysis.executes.set(
                                        software_method_items
                                    )
                                if has_output_items:
                                    RegressionAnalysis.has_outputs.set(has_output_items)
                                if has_input_items:
                                    RegressionAnalysis.has_inputs.set(has_input_items)
                            elif _type_info.name == "Descriptive statistics":
                                DescriptiveStatistics, created = (
                                    DescriptiveStatisticsModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "DescriptiveStatistics",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if has_output_items:
                                    DescriptiveStatistics.has_outputs.set(
                                        has_output_items
                                    )
                                if software_method_items:
                                    DescriptiveStatistics.executes.set(
                                        software_method_items
                                    )
                                if has_input_items:
                                    DescriptiveStatistics.has_inputs.set(
                                        has_input_items
                                    )
                            elif _type_info.name == "Algorithm evaluation":
                                AlgorithmEvaluation, created = (
                                    AlgorithmEvaluationModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "schema_type": _type_info,
                                            "type": "AlgorithmEvaluation",
                                            "statement_id": statement.id,
                                            "evaluates_for": evaluates_for_item,
                                            "evaluate": evaluate_item,
                                        },
                                    )
                                )
                                if has_output_items:
                                    AlgorithmEvaluation.has_outputs.set(
                                        has_output_items
                                    )
                                if software_method_items:
                                    AlgorithmEvaluation.executes.set(
                                        software_method_items
                                    )
                                if has_input_items:
                                    AlgorithmEvaluation.has_inputs.set(has_input_items)

                else:
                    print("no", p)

        return True

    # except Exception as e:
    #     logger.error(f"Error in add_article: {str(e)}")
    #     raise DatabaseError(f"Failed to add article: {str(e)}")

    def _convert_article_to_paper(self, article: ArticleModel) -> Article:
        authors = []
        print("--------_convert_article_to_paper-----------", __file__)
        for author in article.authors.all():
            authors.append(
                Author(
                    id=author.id,
                    orcid=author.orcid,
                    given_name=author.given_name,
                    family_name=author.family_name,
                    author_id=author.author_id,
                    name=author.name,
                    affiliation={
                        "organization_id": author.affiliation.organization_id,
                        "name": author.affiliation.name,
                        "url": author.affiliation.url,
                    },
                )
            )

        all_related_items = []
        for related_item in article.all_related_items:
            items = article.all_related_items[related_item]
            for item in items:
                item_authors = []
                for author in item.get_authors:
                    item_authors.append(
                        {
                            "name": author["name"],
                            "author_id": author["author_id"],
                            "family_name": author["family_name"],
                            "orcid": author["orcid"],
                        }
                    )
                result = {
                    "id": getattr(item, "scholarly_article_id", None)
                    or item.dataset_id,
                    "name": item.name,
                    "abstract": getattr(item, "abstract", None) or item.description,
                    "authors": item_authors,
                }
                if getattr(item, "is_part_of", None):
                    result["publication_issue"] = {
                        "date_published": getattr(
                            item.is_part_of, "date_published", None
                        ),
                        "type": "Article",
                        "periodical": getattr(item.is_part_of.is_part_of, "name", None),
                        "periodical_url": getattr(
                            item.is_part_of.is_part_of, "periodical_id", None
                        ),
                        "publisher_name": getattr(
                            item.is_part_of.is_part_of.publisher, "name", None
                        ),
                        "publisher_url": getattr(
                            item.is_part_of.is_part_of.publisher, "url", None
                        ),
                    }

                if getattr(item, "publisher", None):
                    ts = getattr(item, "date_published", None)
                    year = None
                    if ts:
                        if isinstance(ts, (int, float)):
                            year = datetime.fromtimestamp(ts).year
                        elif isinstance(ts, datetime):
                            year = ts.year
                        elif isinstance(ts, str):
                            year = datetime.fromisoformat(ts).year

                    result["publication_issue"] = {
                        "date_published": year,
                        "type": "Dataset",
                        "periodical": getattr(item.publisher, "name", None),
                        "periodical_url": getattr(item.publisher, "url", None),
                        "publisher_name": "",
                        "publisher_url": "",
                    }

                all_related_items.append(result)

        concepts = []
        for concept in article.concepts.all():
            concepts.append(Concept(id=concept.concept_id, label=concept.label))

        research_fields = []
        for research_field in article.get_research_fields():
            research_fields.append(
                ResearchField(
                    id=research_field["research_field_id"],
                    label=research_field["label"],
                    # related_identifier=research_field.related_identifier,
                    research_field_id=research_field["research_field_id"],
                )
            )

        return Article(
            id=article.id,
            name=article.name,
            authors=authors,
            abstract=article.description,
            contributions=[],
            statements=article.statements.all(),
            dois=article.reborn_doi,
            date_published=article.date_published,
            research_fields=research_fields,
            related_items=all_related_items,
            entity=None,
            external=None,
            info={},
            timeline={},
            publisher=article.publisher,
            # research_fields=research_fields,
            article_id=article.article_id,
            reborn_doi=article.reborn_doi,
            paper_type=article.research_types,
            concepts=concepts,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
