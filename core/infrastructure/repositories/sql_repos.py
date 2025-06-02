import logging
import math
import sys
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from django.db.models import Q, F, Count
from django.core.paginator import Paginator
from django.conf import settings
import json
import hashlib
from datetime import datetime

from core.application.interfaces.repositories import (
    PaperRepository,
    StatementRepository,
    AuthorRepository,
    ConceptRepository,
    ResearchFieldRepository,
    JournalRepository,
)
from core.infrastructure.clients.type_registry_client import TypeRegistryClient
from core.application.mappers.entity_mappers import (
    PaperMapper,
    StatementMapper,
    AuthorMapper,
    ConceptMapper,
    ResearchFieldMapper,
)
from core.application.dtos.output_dtos import ShortPaperOutputDTO, ShortAuthorOutputDTO
from core.domain.entities import (
    Paper,
    Statement,
    Author,
    Concept,
    ResearchField,
    Journal,
    Conference,
    Notation,
    Contribution,
)
from core.domain.exceptions import EntityNotFound, DatabaseError
from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
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
    Contribution as ContributionModel,
)
from core.infrastructure.scrapers.node_extractor import NodeExtractor

logger = logging.getLogger(__name__)


def generate_static_id(input_string: str) -> str:
    """Generate a static ID from a string."""
    hash_object = hashlib.sha256(input_string.encode("utf-8"))
    return hash_object.hexdigest()[:32]


def fetch_reborn_doi(doi: str) -> str:
    """Fetch the reborn DOI from a regular DOI."""
    import requests

    url = "https://api.datacite.org/dois"
    query = f'relatedIdentifiers.relatedIdentifier:"{doi.replace("https://doi.org/", "")}" AND relatedIdentifiers.relationType:IsVariantFormOf'
    params = {"query": query}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("data"):
            return ""

        return f"https://doi.org/{result['data'][0]['id']}"

    except Exception as e:
        logger.error(f"Error fetching reborn DOI: {str(e)}")
        return ""


class SQLPaperRepository(PaperRepository):
    """PostgreSQL implementation of the Paper repository."""

    def __init__(self, type_registry_client: TypeRegistryClient):
        """Initialize the repository."""
        self.type_registry_client = type_registry_client
        self.scraper = NodeExtractor()

    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Paper], int]:
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

    def find_by_id(self, paper_id: str) -> Optional[Paper]:
        """Find a paper by its ID."""
        print("---------------find_by_id------------=============------", __file__)
        try:
            article = ArticleModel.objects.filter(article_id=paper_id).first()
            if article:
                return self._convert_article_to_paper(article)

            return None

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve paper: {str(e)}")

    def search_by_title(self, title: str) -> List[Paper]:
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
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        author_ids: Optional[List[str]] = None,
        journal_names: Optional[List[str]] = None,
        concept_ids: Optional[List[str]] = None,
        conference_names: Optional[List[str]] = None,
        title: Optional[str] = None,
        research_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Paper], int]:
        """Query papers with filters."""
        try:
            query = ArticleModel.objects.all()

            if title:
                query = query.filter(
                    Q(name__icontains=title)
                    | Q(statements__supports__contains=[{"notation": {"label": title}}])
                )

            if author_ids and len(author_ids) > 0:
                query = query.filter(authors__id__in=author_ids)

            if journal_names and len(journal_names) > 0:
                # Filter based on journal data in JSONField
                journals_filter = Q()
                for name in journal_names:
                    journals_filter |= Q(journal__label__icontains=name)
                query = query.filter(journals_filter)

            if concept_ids and len(concept_ids) > 0:
                query = query.filter(concepts__id__in=concept_ids)

            if start_year and end_year:
                start_date = datetime(int(start_year), 1, 1)
                end_date = datetime(int(end_year), 12, 31)
                query = query.filter(date_published__range=[start_date, end_date])

            if research_fields and len(research_fields) > 0:
                query = query.filter(research_fields_id__overlap=research_fields)

            # Get total count before pagination
            total = query.count()

            # Apply pagination
            paginator = Paginator(query.order_by("name"), page_size)
            page_obj = paginator.get_page(page)

            papers = []
            for article in page_obj:
                paper = self._convert_article_to_paper(article)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in query_papers: {str(e)}")
            raise DatabaseError(f"Failed to query papers: {str(e)}")

    def save(self, paper: Paper) -> Paper:
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

    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Paper], int]:
        """Get latest articles with filters."""
        try:
            query = ArticleModel.objects.all()
            print("-----------get_latest_articles---------", __file__)
            if search_query:
                query = query.filter(name__icontains=search_query)

            if research_fields and len(research_fields) > 0:
                query = query.filter(research_fields_id__overlap=research_fields)

            # Apply sorting
            if sort_order == "a-z":
                query = query.order_by("name")
            elif sort_order == "z-a":
                query = query.order_by("-name")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("name")

            # Get total count before pagination
            total = query.count()

            # Apply pagination
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            papers = []
            for article in page_obj:
                paper = self._convert_article_to_paper(article)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in get_latest_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest articles: {str(e)}")

    def get_semantics_articles(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Paper], int]:
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
        # print("len(info): ", len(info))
        # print(info)
        _type = info["@type"]
        if f"{_type}#{property}" in info:
            return info[f"{_type}#{property}"]
        elif f"{_type}#{property}".replace("doi:", "doi:21.T11969/") in info:
            return info[f"{_type}#{property}".replace("doi:", "doi:21.T11969/")]

    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        scraper = NodeExtractor()
        graph_data = paper_data.get("@graph", [])
        data = {}
        data["Dataset"] = [
            item for item in graph_data if "Dataset" in item.get("@type", [])
        ]

        data["researchField"] = [
            item for item in graph_data if "ResearchField" in item.get("@type", [])
        ]
        research_fields = []
        for research_field in data["researchField"]:
            rf, created = ResearchFieldModel.objects.get_or_create(
                _id=research_field.get("@id", ""),
                label=research_field["label"],
                research_field_id=generate_static_id(research_field["label"]),
                defaults={
                    "label": research_field["label"],
                    "json": research_field,
                    "research_field_id": generate_static_id(research_field["label"]),
                },
            )
            research_fields.append(rf)

        data["author"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Person" or "Person" in item.get("@type"))
        ]
        authors = []
        authors_id = {}
        for author in data["author"]:
            author_obj, created = AuthorModel.objects.get_or_create(
                _id=author.get("@id", ""),
                defaults={
                    "orcid": author.get("@id", ""),
                    "json": author,
                    "author_id": generate_static_id(
                        f"{author.get('givenName', '')} {author.get('familyName', '')}"
                    ),
                    "given_name": author.get("givenName", ""),
                    "family_name": author.get("familyName", ""),
                    "label": f"{author.get('givenName', '')} {author.get('familyName', '')}",
                },
            )
            authors_id[author.get("@id", "")] = author_obj.id
            authors.append(author_obj)

        data["unit"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Unit" or "Unit" in item.get("@type"))
        ]
        units = []
        units_id = {}
        for unit in data["unit"]:
            unit_obj, created = UnitModel.objects.get_or_create(
                _id=unit.get("@id", ""),
                defaults={
                    "json": unit,
                    "type": unit.get("@type", ""),
                    "exact_match": unit.get("exactMatch", "")
                    if len(unit.get("exactMatch", "")) > 0
                    else [],
                    "label": unit.get("label", "")
                    if len(unit.get("label", "")) > 0
                    else [],
                },
            )
            units_id[unit.get("@id", "")] = unit_obj.id
            units.append(unit_obj)

        data["objectOfInterest"] = [
            item
            for item in graph_data
            if (
                item.get("@type") == "ObjectOfInterest"
                or "ObjectOfInterest" in item.get("@type")
            )
        ]
        objectOfInterests = []
        objectOfInterests_id = {}
        for objectOfInterest in data["objectOfInterest"]:
            objectOfInterest_obj, created = ObjectOfInterestModel.objects.get_or_create(
                _id=objectOfInterest.get("@id", ""),
                defaults={
                    "json": objectOfInterest,
                    "type": objectOfInterest.get("@type", ""),
                    "exact_match": objectOfInterest.get("exactMatch", "")
                    if len(objectOfInterest.get("exactMatch", "")) > 0
                    else [],
                    "close_match": objectOfInterest.get("closeMatch", "")
                    if len(objectOfInterest.get("closeMatch", "")) > 0
                    else [],
                    "label": objectOfInterest.get("label", "")
                    if len(objectOfInterest.get("label", "")) > 0
                    else [],
                },
            )
            objectOfInterests_id[objectOfInterest.get("@id", "")] = (
                objectOfInterest_obj.id
            )
            objectOfInterests.append(objectOfInterest_obj)

        data["matrix"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Matrix" or "Matrix" in item.get("@type"))
        ]

        matrices = []
        matrices_id = {}
        for matrix in data["matrix"]:
            matrix_obj, created = MatrixModel.objects.get_or_create(
                _id=matrix.get("@id", ""),
                defaults={
                    "json": matrix,
                    "exact_match": matrix.get("exactMatch", "")
                    if len(matrix.get("exactMatch", "")) > 0
                    else [],
                    "close_match": matrix.get("closeMatch", "")
                    if len(matrix.get("closeMatch", "")) > 0
                    else [],
                    "label": matrix.get("label", "")
                    if len(matrix.get("label", "")) > 0
                    else [],
                },
            )
            matrices_id[matrix.get("@id", "")] = matrix_obj.id
            matrices.append(matrix_obj)

        data["property"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Property" or "Property" in item.get("@type"))
        ]
        properties = []
        properties_id = {}
        for property in data["property"]:
            property_obj, created = PropertyModel.objects.get_or_create(
                _id=property.get("@id", ""),
                defaults={
                    "json": property,
                    "exact_match": property.get("exactMatch", "")
                    if len(property.get("exactMatch", "")) > 0
                    else [],
                    "close_match": property.get("closeMatch", "")
                    if len(property.get("closeMatch", "")) > 0
                    else [],
                    "label": property.get("label", "")
                    if len(property.get("label", "")) > 0
                    else [],
                },
            )
            properties_id[property.get("@id", "")] = property_obj.id
            properties.append(property_obj)

        data["constraint"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Constraint" or "Constraint" in item.get("@type"))
        ]
        constraints = []
        constraints_id = {}
        for constraint in data["constraint"]:
            constraint_obj, created = ConstraintModel.objects.get_or_create(
                _id=constraint.get("@id", ""),
                defaults={
                    "json": constraint,
                    "exact_match": constraint.get("exactMatch", "")
                    if len(constraint.get("exactMatch", "")) > 0
                    else [],
                    "close_match": constraint.get("closeMatch", "")
                    if len(constraint.get("closeMatch", "")) > 0
                    else [],
                    "label": constraint.get("label", "")
                    if len(constraint.get("label", "")) > 0
                    else [],
                },
            )
            constraints_id[constraint.get("@id", "")] = constraint_obj.id
            constraints.append(constraint_obj)

        data["operation"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Operation" or "Operation" in item.get("@type"))
        ]
        operations = []
        operations_id = {}
        for operation in data["operation"]:
            operation_obj, created = OperationModel.objects.get_or_create(
                _id=operation.get("@id", ""),
                defaults={
                    "json": operation,
                    "exact_match": operation.get("exactMatch", "")
                    if len(operation.get("exactMatch", "")) > 0
                    else [],
                    "close_match": operation.get("closeMatch", "")
                    if len(operation.get("closeMatch", "")) > 0
                    else [],
                    "label": operation.get("label", "")
                    if len(operation.get("label", "")) > 0
                    else [],
                },
            )
            operations_id[operation.get("@id", "")] = operation_obj.id
            operations.append(operation_obj)

        types = ["Component", "Variable", "Measure"]
        items = []
        items_id = {}
        for _type in types:
            data[_type] = [
                item
                for item in graph_data
                if (item.get("@type") == _type or _type in item.get("@type"))
            ]
            for component in data[_type]:
                component_obj, created = ComponentModel.objects.get_or_create(
                    _id=component.get("@id", ""),
                    defaults={
                        "json": component,
                        "type": component.get("@type", ""),
                        "string_match": component.get("stringMatch", "")
                        if len(component.get("stringMatch", "")) > 0
                        else [],
                        "exact_match": component.get("exactMatch", "")
                        if len(component.get("exactMatch", "")) > 0
                        else [],
                        "close_match": component.get("closeMatch", "")
                        if len(component.get("closeMatch", "")) > 0
                        else [],
                    },
                )
                items_id[component.get("@id", "")] = component_obj.id
                items.append(component_obj)

                if component.get("matrix", None) is not None:
                    component_obj.matrices.add(
                        matrices_id[component.get("matrix", None)["@id"]]
                    )

                if component.get("objectOfInterest", None) is not None:
                    component_obj.object_of_interests.add(
                        objectOfInterests_id[
                            component.get("objectOfInterest", None)["@id"]
                        ]
                    )

                if component.get("property", None) is not None:
                    component_obj.properties.add(
                        properties_id[component.get("property", None)["@id"]]
                    )

                if component.get("unit", None) is not None:
                    component_obj.units.set(
                        [units_id[component.get("unit", None)["@id"]]]
                    )

        data["publisher"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Publisher" or "Publisher" in item.get("@type"))
        ]
        for publisher in data["publisher"]:
            publisher_obj, created = PublisherModel.objects.get_or_create(
                _id=publisher.get("@id", ""),
                defaults={
                    "label": publisher.get("label", ""),
                    "publisher_id": generate_static_id(publisher.get("label", "")),
                    "json": publisher,
                },
            )
            publisher_id = publisher_obj.id

        journal_id = False
        data["journal"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Journal" or "Journal" in item.get("@type"))
        ]
        for journal in data["journal"]:
            journal_obj, created = JournalConferenceModel.objects.get_or_create(
                _id=journal.get("@id", ""),
                defaults={
                    "label": journal.get("label", ""),
                    "journal_conference_id": generate_static_id(
                        journal.get("label", "")
                    ),
                    "json": journal,
                    "type": "journal",
                    "publisher_id": publisher_id,
                },
            )
            journal_id = journal_obj.id
            journal_obj.research_fields.set(research_fields)

        data["conference"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Conference" or "Conference" in item.get("@type"))
        ]
        conference_id = False
        for conference in data["conference"]:
            conference_obj, created = JournalConferenceModel.objects.get_or_create(
                _id=conference.get("@id", ""),
                defaults={
                    "label": conference.get("label", ""),
                    "journal_conference_id": generate_static_id(
                        conference.get("label", "")
                    ),
                    "json": conference,
                    "type": "conference",
                    "publisher_id": publisher_id,
                },
            )
            conference_id = conference_obj.id
            conference_obj.research_fields.set(research_fields)

        data["concept"] = [
            item
            for item in graph_data
            if (item.get("@type") == "Concept" or "Concept" in item.get("@type"))
        ]
        concepts = []
        concepts_id = {}
        for concept in data["concept"]:
            concept_obj, created = ConceptModel.objects.get_or_create(
                _id=concept.get("@id", ""),
                concept_id=generate_static_id(concept.get("label", "")),
                defaults={
                    "label": concept.get("label", ""),
                    "json": concept,
                    "definition": concept.get("definition", ""),
                    "see_also": concept.get("seeAlso", ""),
                    "string_match": concept.get("stringMatch", ""),
                    "concept_id": generate_static_id(concept.get("label", "")),
                },
            )
            concepts_id[concept.get("@id", "")] = concept_obj.id
            concepts.append(concept_obj)

        article_data = [
            item
            for item in graph_data
            if (
                item.get("@type") == "ScholarlyArticle"
                or "ScholarlyArticle" in item.get("@type")
            )
        ][0]

        if not article_data:
            logger.error("No ScholarlyArticle found in data")
            return False

        article, created = ArticleModel.objects.update_or_create(
            _id=article_data.get("@id", ""),
            defaults={
                "name": article_data.get("name", ""),
                "article_id": generate_static_id(article_data.get("name", "")),
                "json": article_data,
                "abstract": article_data.get("abstract", ""),
                "date_published": datetime.strptime(
                    article_data.get("datePublished", ""), "%Y"
                )
                if isinstance(article_data.get("datePublished"), str)
                else None,
                "identifier": article_data.get("identifier", ""),
                "reborn_doi": fetch_reborn_doi(article_data.get("@id", "")),
                "publisher_id": publisher_id,
                "journal_conference_id": conference_id if conference_id else journal_id,
                "paper_type": "conference" if conference_id else "journal",
            },
        )
        article.authors.set(authors)
        article.concepts.set(concepts)
        article.research_fields.set(research_fields)

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
        # print(data["statements"])
        # print('----------data["json_files"]------------')
        # print(data["json_files"])
        # print('----------data["json_files"]------------')
        # iii = 0
        for statement_item in data["json_files"]:
            # print("---------------------------------")
            # print("json file: ", statement_item.get("name", ""))
            # print("json file: ", statement_item)
            # iii += 1
            # if iii > 3:
            #     continue
            statement_content = scraper.load_json_from_url(
                json_files[statement_item.get("name", "")]
            )
            print("----------------statement_content-----------------")
            # print(statement_content)
            # print("----------------statement_content-----------------")
            # print("----------------statement_item-----------------")
            # print(statement_item.get("components", ""))
            # print("----------------statement_item-----------------")
            if not statement_content:
                continue

            statement_properties = {}
            statement_properties["components"] = statement_item.get("components", "")
            statement_properties["json_files"] = json_files[
                statement_item.get("name", "")
            ]
            for support in statement_item.get("supports", ""):
                notation = data["LinguisticStatement"][
                    data["statements"][support["@id"]]["notation"]["@id"]
                ]
                statement_properties["author"] = data["statements"][support["@id"]][
                    "author"
                ]
                statement_properties["label"] = notation["label"]
                statement_properties["concept"] = notation["concept"]

            statement, created = StatementModel.objects.update_or_create(
                _id=statement_item["@id"],
                defaults={
                    "label": statement_properties["label"],
                    "statement_id": generate_static_id(statement_properties["label"]),
                    "name": json_files[statement_item.get("name", "")],
                    "json": statement_item,
                    "content": statement_content,
                    "article_id": article.id,
                    "version": statement_item["version"],
                    "encodingFormat": statement_item["encodingFormat"],
                },
            )
            for component in statement_item.get("components", ""):
                statement.components.add(items_id[component["@id"]])

            for concept in statement_properties["concept"]:
                statement.concepts.add(concepts_id[concept["@id"]])

            for author in statement_properties["author"]:
                statement.authors.add(authors_id[author["@id"]])

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
                        # print("#is_implemented_by")
                        # print(statement_content[p])
                        implement, created = ImplementModel.objects.update_or_create(
                            url=statement_content[p],
                            statement_id=statement.id,
                            defaults={
                                "url": statement_content[p],
                                "statement_id": statement.id,
                            },
                        )
                    elif p.endswith("#has_part"):
                        # print("#has_part")
                        has_parts = statement_content[p]
                        if isinstance(statement_content[p], dict):
                            has_parts = [statement_content[p]]

                        for statement_content_item in has_parts:
                            _type_info, _info = self.type_registry_client.get_type_info(
                                statement_content_item["@type"].replace("doi:", "")
                            )
                            label_items = [
                                item for item in _info["property"] if "#label" in item
                            ]
                            print("------------statement_id-----------")

                            HasPartModel.objects.update_or_create(
                                label=statement_content_item[label_items[0]]
                                if label_items[0] in statement_content_item
                                else "",
                                statement_id=statement.id,
                                defaults={
                                    "label": statement_content_item[label_items[0]]
                                    if label_items[0] in statement_content_item
                                    else "",
                                    "statement_id": statement.id,
                                    "type": _info["name"],
                                    "schema_type": _type_info,
                                    "description": _info["description"],
                                },
                            )
                            label = ""
                            see_also = ""
                            target_item = ""
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
                                            figure, created = (
                                                FigureModel.objects.update_or_create(
                                                    source_url=has_expression_source_url,
                                                    label=has_expression_label,
                                                    defaults={
                                                        "label": has_expression_label,
                                                        "source_url": has_expression_source_url,
                                                    },
                                                )
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
                                                },
                                            )
                                        )
                                        if has_expressions:
                                            data_item.has_expression.set(
                                                has_expressions
                                            )
                                        if has_output_has_parts:
                                            data_item.has_part.set(has_output_has_parts)

                                        has_output_items.append(data_item)
                                elif _p.endswith("#has_input"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#has_input",
                                        _p,
                                    )
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

                                        has_expressions = None
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
                                                },
                                            )
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
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#evaluates_for",
                                        _p,
                                    )
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
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#evaluates",
                                        _p,
                                    )
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
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "Done #executes",
                                        _p,
                                    )
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

                                        software_item, created = (
                                            SoftwareModel.objects.update_or_create(
                                                has_support_url=softwares_has_support_url,
                                                version_info=softwares_version_info,
                                                label=softwares_label,
                                                defaults={
                                                    "has_support_url": softwares_has_support_url,
                                                    "version_info": softwares_version_info,
                                                    "label": softwares_label,
                                                },
                                            )
                                        )
                                        software_libraries_item, created = (
                                            SoftwareLibraryModel.objects.update_or_create(
                                                has_support_url=software_libraries_has_support_url,
                                                version_info=software_libraries_version_info,
                                                label=software_libraries_label,
                                                defaults={
                                                    "has_support_url": software_libraries_has_support_url,
                                                    "version_info": software_libraries_version_info,
                                                    "part_of": software_item,
                                                    "label": software_libraries_label,
                                                },
                                            )
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
                                        software_method_item, created = (
                                            SoftwareMethodModel.objects.update_or_create(
                                                has_support_url=software_method_has_support_url,
                                                is_implemented_by=software_method_is_implemented_by,
                                                label=software_method_label,
                                                defaults={
                                                    "has_support_url": software_method_has_support_url,
                                                    "is_implemented_by": software_method_is_implemented_by,
                                                    "label": software_method_label,
                                                },
                                            )
                                        )
                                        software_method_item.part_of.add(
                                            software_libraries_item
                                        )
                                        software_method_items.append(
                                            software_method_item.id
                                        )
                                elif _p.endswith("#targets"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "Done #targets",
                                        _p,
                                    )
                                    target = statement_content_item[_p]
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
                                elif _p.endswith("#label"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#label",
                                        _p,
                                    )
                                    label = statement_content_item[_p]
                                elif _p.endswith("#level"):
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#level",
                                        _p,
                                    )
                                    levels = statement_content_item[_p]
                                    if not isinstance(levels, list):
                                        levels = [levels]
                                    level_items = []
                                    for level in levels:
                                        print('------------level["@type"]-----------')
                                        print(levels)
                                        print(level)
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
                                    print(
                                        f"Line: {sys._getframe(0).f_lineno}",
                                        "#see_also",
                                        _p,
                                    )
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

                            print(_type_info.name)
                            print(software_method_items)
                            if _type_info.name == "Multilevel analysis":
                                MultilevelAnalysis, created = (
                                    MultilevelAnalysisModel.objects.update_or_create(
                                        statement_id=statement.id,
                                        label=label,
                                        defaults={
                                            "label": label,
                                            "see_also": see_also,
                                            "type": "MultilevelAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_item:
                                    MultilevelAnalysis.targets.add(target_item)
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
                                            "type": "ClassPrediction",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_item:
                                    ClassPrediction.targets.add(target_item)
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
                                            "type": "GroupComparison",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_item:
                                    GroupComparison.targets.add(target_item)
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
                                            "type": "RegressionAnalysis",
                                            "statement_id": statement.id,
                                        },
                                    )
                                )
                                if target_item:
                                    RegressionAnalysis.targets.add(target_item)
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
                        print("---------p-------------")
                        print(p)
                        print("---------statement_content[p]-------------")
                        print(statement_content[p])
                        print("---------statement_content-------------")
                        # print(statement_content)
                        # _type_info, _info = self.type_registry_client.get_type_info(
                        #     statement_content[p]["@type"].replace("doi:", "")
                        # )

                    # DescriptiveStatisticsModel,
                    # GroupComparisonModel,
                    # MultilevelAnalysisModel,
                    # FactorAnalysisModel,
                    # data_type, created = DataTypeModel.objects.update_or_create(
                    #     url=statement_content[p],
                    #     statement_id=statement.id,
                    #     defaults={
                    #         "url": statement_content[p],
                    #         "statement_id": statement.id,
                    #     },
                    # )
                else:
                    print("no", p)
            print("**********statement_content**********")

        # Add to search index
        article_data = [
            {
                "title": article.name,
                "abstract": article.abstract,
                "article_id": article.id,
            }
        ]

        # Import here to avoid circular import
        # from core.infrastructure.search.hybrid_engine import HybridSearchEngine
        # from core.infrastructure.search.semantic_engine import SemanticSearchEngine
        # from core.infrastructure.search.keyword_engine import KeywordSearchEngine

        # semantic_engine = SemanticSearchEngine()
        # keyword_engine = KeywordSearchEngine()
        # hybrid_engine = HybridSearchEngine(semantic_engine, keyword_engine)

        # hybrid_engine.semantic_engine.add_articles(article_data)
        # hybrid_engine.keyword_engine.add_articles(article_data)

        return True

    # except Exception as e:
    #     logger.error(f"Error in add_article: {str(e)}")
    #     raise DatabaseError(f"Failed to add article: {str(e)}")

    def _convert_article_to_paper(self, article: ArticleModel) -> Paper:
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
                    label=author.label,
                )
            )
        journal = None
        if article.journal_conference:
            journal = Journal(
                id=article.journal_conference.id,
                label=article.journal_conference.label,
                journal_conference_id=article.journal_conference.journal_conference_id,
                publisher=article.publisher_id,
            )

        concepts = []
        for concept in article.concepts.all():
            concepts.append(Concept(id=concept.concept_id, label=concept.label))

        print("--------------find_by_id-----00000000000000-------", __file__)
        research_fields = []
        for research_field in article.research_fields.all():
            research_fields.append(
                ResearchField(
                    id=research_field.id,
                    label=research_field.label,
                    research_field_id=research_field.research_field_id,
                )
            )
        return Paper(
            id=article.id,
            name=article.name,
            authors=authors,
            abstract=article.abstract,
            contributions=[],
            statements=article.statements.all(),
            dois=article.identifier,
            date_published=article.date_published,
            research_fields=research_fields,
            entity=None,
            external=None,
            info={},
            timeline={},
            journal=journal,
            publisher=article.publisher,
            # research_fields=research_fields,
            article_id=article.article_id,
            reborn_doi=article.reborn_doi,
            paper_type=article.paper_type,
            concepts=concepts,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )


class SQLAuthorRepository(AuthorRepository):
    """PostgreSQL implementation of the Author repository."""

    def find_by_name(self, name: str) -> List[Author]:
        """Find authors by name."""
        try:
            authors_queryset = AuthorModel.objects.filter(
                Q(label__icontains=name)
                | Q(given_name__icontains=name)
                | Q(family_name__icontains=name)
            ).order_by("label")[:10]  # Limit to 10 authors

            authors = []
            for author_model in authors_queryset:
                author = Author(
                    id=author_model.id,
                    orcid=author_model.orcid,
                    given_name=author_model.given_name,
                    family_name=author_model.family_name,
                    label=author_model.label,
                )
                authors.append(author)

            return authors

        except Exception as e:
            logger.error(f"Error in find_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find authors: {str(e)}")

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


class SQLConceptRepository(ConceptRepository):
    """PostgreSQL implementation of the Concept repository."""

    def find_by_label(self, label: str) -> List[Concept]:
        """Find concepts by label."""
        try:
            concepts_queryset = ConceptModel.objects.filter(
                label__icontains=label
            ).order_by("label")[:10]  # Limit to 10 concepts

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


class SQLResearchFieldRepository(ResearchFieldRepository):
    """PostgreSQL implementation of the ResearchField repository."""

    def find_by_label(self, label: str) -> List[ResearchField]:
        """Find research fields by label."""
        try:
            rf_queryset = ResearchFieldModel.objects.filter(
                label__icontains=label
            ).order_by("label")[:10]  # Limit to 10 research fields

            research_fields = []
            for rf_model in rf_queryset:
                research_field = ResearchField(
                    id=rf_model.id,
                    label=rf_model.label,
                    research_field_id=rf_model.research_field_id,
                )
                research_fields.append(research_field)

            return research_fields

        except Exception as e:
            logger.error(f"Error in find_by_label: {str(e)}")
            raise DatabaseError(f"Failed to find research fields: {str(e)}")

    def save(self, research_field: ResearchField) -> ResearchField:
        """Save a research field."""
        try:
            if not research_field.id:
                research_field.id = generate_static_id(research_field.label)

            # Create or update research field
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


class SQLJournalRepository(JournalRepository):
    """PostgreSQL implementation of the Journal repository."""

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find journals by name."""
        try:
            journals_queryset = JournalConferenceModel.objects.filter(
                label__icontains=name
            ).order_by("label")[:10]  # Limit to 10 journals

            journals = []
            for journal_model in journals_queryset:
                journal_dict = {
                    "id": journal_model.id,
                    "label": journal_model.label,
                    "publisher": journal_model.publisher,
                }
                journals.append(journal_dict)

            return journals

        except Exception as e:
            logger.error(f"Error in find_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find journals: {str(e)}")

    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get latest journals with filters."""
        print("-------------get_latest_journals----------", __file__)
        try:
            query = JournalConferenceModel.objects.all()

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

            journals = []
            for journal_model in page_obj:
                journal_dict = {
                    "id": journal_model.id,
                    "journal_conference_id": journal_model.journal_conference_id,
                    "label": journal_model.label,
                    "publisher": journal_model.publisher,
                }
                journals.append(journal_dict)
            return journals, total

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest journals: {str(e)}")


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

    def find_paper_with_statement_details(
        self, statement_id: str
    ) -> Optional[Statement]:
        """Find a statement by its ID."""
        try:
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

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statement: {str(e)}")

    def find_by_id(self, statement_id: str) -> Optional[Statement]:
        """Find a statement by its ID."""
        try:
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

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statement: {str(e)}")

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
    ) -> Paper:
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
                    label=author.label,
                )
            )
        journal = None
        if article.journal_conference:
            journal = Journal(
                id=article.journal_conference.id,
                label=article.journal_conference.label,
                publisher=article.publisher_id,
            )

        concepts = []
        for concept in article.concepts.all():
            concepts.append(Concept(id=concept.concept_id, label=concept.label))

        print("--------------find_by_id----1111111111111--------", __file__)
        return Paper(
            id=article.id,
            name=article.name,
            authors=authors,
            abstract=article.abstract,
            contributions=[],
            statements=article.statements.all(),
            dois=article.identifier,
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
            paper_type=article.paper_type,
            concepts=concepts,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        print("----------get_latest_statements------", __file__)
        try:
            query = StatementModel.objects.select_related("article").all()
            if search_query:
                query = query.filter(
                    supports__contains=[{"notation": {"label": search_query}}]
                )

            if research_fields and len(research_fields) > 0:
                query = query.filter(research_fields_id__overlap=research_fields)

            if sort_order == "a-z":
                query = query.order_by("article__name")
            elif sort_order == "z-a":
                query = query.order_by("-article__name")
            elif sort_order == "newest":
                query = query.order_by("-created_at")
            else:
                query = query.order_by("article__name")

            total = query.count()
            paginator = Paginator(query, page_size)
            page_obj = paginator.get_page(page)

            statements = []
            for statement_model in page_obj:
                statement = self._convert_statement_to_entity(statement_model)
                statements.append(statement)
            return statements, total

        except Exception as e:
            logger.error(f"Error in get_latest_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest statements: {str(e)}")

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
        print("----------_convert_statement_to_entity------", __file__)
        authors = []
        for author in statement_model.authors.all():
            print(author.author_id)
            authors.append(
                Author(
                    id=author.id,
                    author_id=author.author_id,
                    given_name=author.given_name,
                    orcid=author.orcid,
                    family_name=author.family_name,
                    label=author.label,
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
                        label=author_data.get("label", ""),
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
                    label=author.label,
                )
            )
        journal = None
        if statement_model.article.journal_conference:
            journal = Journal(
                id=statement_model.article.journal_conference.id,
                label=statement_model.article.journal_conference.label,
                publisher=statement_model.article.publisher_id,
            )

        article_concepts = []
        for concept in statement_model.article.concepts.all():
            article_concepts.append(Concept(id=concept.concept_id, label=concept.label))
        article = {
            "concepts": article_concepts,
            "journal": journal,
            "authors": article_authors,
            "abstract": statement_model.article.abstract,
            "dois": statement_model.article.identifier,
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
            journal_conference=statement_model.article.journal_conference.label,
            statement_id=statement_model.statement_id,
            created_at=statement_model.created_at,
            updated_at=statement_model.updated_at,
        )
