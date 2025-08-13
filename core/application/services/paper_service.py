import logging
import math
import os
from typing import List, Dict, Any, Optional
from django.core.cache import cache
from django.utils.timezone import localtime
from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.repositories.statement import StatementRepository
from core.application.interfaces.services.paper import (
    PaperService as PaperServiceInterface,
)

from core.application.dtos.input_dtos import (
    QueryFilterInputDTO,
    ScraperUrlInputDTO,
)
from core.application.dtos.output_dtos import (
    PaperOutputDTO,
    ShortPaperOutputDTO,
    StatementOutputDTO,
    AuthorOutputDTO,
    ShortAuthorOutputDTO,
    ShortStatementOutputDTO,
    ConceptOutputDTO,
    CommonResponseDTO,
    PaginatedResponseDTO,
)
from rest_framework.response import Response
from core.domain.exceptions import (
    DatabaseError,
)
from core.infrastructure.scrapers.node_extractor import NodeExtractor

logger = logging.getLogger(__name__)


class PaperServiceImpl(PaperServiceInterface):
    """Implementation of the paper service."""

    def __init__(
        self,
        paper_repository: PaperRepository,
        statement_repository: StatementRepository,
        author_repository: AuthorRepository,
        concept_repository: ConceptRepository,
        research_field_repository: ResearchFieldRepository,
        journal_repository: JournalRepository,
    ):
        self.paper_repository = paper_repository
        self.statement_repository = statement_repository
        self.author_repository = author_repository
        self.concept_repository = concept_repository
        self.research_field_repository = research_field_repository
        self.journal_repository = journal_repository
        self.scraper = NodeExtractor()

    def get_all_papers(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all papers with pagination."""
        # cache_key = f"all_papers_{page}_{page_size}"
        # cached_result = cache.get(cache_key)
        print("------------get_all_papers------------", __file__)
        # if cached_result:
        #     return cached_result

        # try:
        papers, total = self.paper_repository.find_all(page, page_size)
        result = PaginatedResponseDTO(
            content=[self._map_paper_to_dto(paper) for paper in papers],
            total_elements=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )

        # Cache for 15 minutes
        # cache.set(cache_key, result, settings.CACHE_TTL)
        return result

        # except Exception as e:
        #     logger.error(f"Error in get_all_papers: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve papers: {str(e)}")

    def get_all_statements(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedResponseDTO:
        """Get all statements with pagination."""
        # cache_key = f"all_statements_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            statements, total = self.statement_repository.find_all(page, page_size)

            result = PaginatedResponseDTO(
                content=[
                    self._map_statement_to_dto(statement) for statement in statements
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_all_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements: {str(e)}")

    def search_by_title(self, title: str) -> List[PaperOutputDTO]:
        """Search papers by title."""
        try:
            papers = self.paper_repository.search_by_title(title)
            return [self._map_paper_to_dto(paper) for paper in papers]

        except Exception as e:
            logger.error(f"Error in search_by_title: {str(e)}")
            raise DatabaseError(f"Failed to search papers: {str(e)}")

    def query_data(self, query_filter: QueryFilterInputDTO) -> PaginatedResponseDTO:
        """Query data with filters."""
        print("------query_data------", __file__)
        # try:
        papers, total = self.paper_repository.query_papers(
            title=query_filter.title,
            start_year=query_filter.start_year,
            end_year=query_filter.end_year,
            author_ids=query_filter.author_ids,
            scientific_venue_ids=query_filter.scientific_venue_ids,
            concept_ids=query_filter.concept_ids,
            research_field_ids=query_filter.research_field_ids,
            page=query_filter.page,
            page_size=query_filter.per_page,
        )

        # Convert Paper objects to serializable dictionaries
        serialized_papers = []
        for paper in papers:
            # Extract authors safely
            authors = []
            if hasattr(paper, "authors") and paper.authors:
                if hasattr(paper.authors, "all"):  # QuerySet
                    authors = [
                        {"id": author.author_id, "label": str(author.label)}
                        for author in paper.authors.all()
                    ]
                elif isinstance(paper.authors, list):  # List
                    authors = [
                        {
                            "id": author.author_id,
                            "label": str(author.label),
                            "orcid": author.orcid,
                        }
                        for author in paper.authors
                    ]
                else:  # Single author
                    authors = [
                        {
                            "id": getattr(paper.authors, "id", ""),
                            "label": str(paper.authors),
                        }
                    ]

            # Extract concepts safely
            concepts = []
            if hasattr(paper, "concepts") and paper.concepts:
                if hasattr(paper.concepts, "all"):  # QuerySet
                    concepts = [
                        {"id": concept.id, "label": concept.label}
                        for concept in paper.concepts.all()
                    ]
                elif isinstance(paper.concepts, list):  # List
                    concepts = [
                        {
                            "id": getattr(concept, "id", ""),
                            "label": getattr(concept, "label", str(concept)),
                        }
                        for concept in paper.concepts
                    ]

            # Extract research fields safely
            research_fields = []
            if hasattr(paper, "research_fields") and paper.research_fields:
                if hasattr(paper.research_fields, "all"):  # QuerySet
                    research_fields = [
                        {
                            "id": rf.research_field_id,
                            "label": rf.label,
                            "identifier": getattr(rf, "_id", str(rf)),
                        }
                        for rf in paper.research_fields.all()
                    ]
                elif isinstance(paper.research_fields, list):  # List
                    research_fields = [
                        {
                            "id": getattr(rf, "research_field_id", ""),
                            "label": getattr(rf, "label", str(rf)),
                            "related_identifier": getattr(
                                rf, "related_identifier", str(rf)
                            ),
                        }
                        for rf in paper.research_fields
                    ]

            # Extract journal/conference safely
            journal_conference = None
            if hasattr(paper, "journal_conference") and paper.journal_conference:
                journal_conference = {
                    "id": getattr(paper.journal_conference, "id", ""),
                    "label": getattr(
                        paper.journal_conference,
                        "label",
                        str(paper.journal_conference),
                    ),
                    "identifier": getattr(paper.journal_conference, "_id", ""),
                }
            elif hasattr(paper, "journal") and paper.journal:
                journal_conference = {
                    "id": getattr(paper.journal, "journal_conference_id", ""),
                    "identifier": getattr(paper.journal, "_id", ""),
                    "label": getattr(paper.journal, "label", str(paper.journal)),
                }

            publisher = None
            if hasattr(paper, "publisher") and paper.publisher:
                publisher = paper.publisher.label
            paper_dict = {
                "article_id": getattr(paper, "article_id", ""),
                "name": getattr(paper, "name", getattr(paper, "title", "")),
                "abstract": getattr(paper, "abstract", ""),
                "date_published": paper.date_published.year
                if hasattr(paper, "date_published")
                and localtime(paper.date_published).strftime("%Y")
                else None,
                "dois": getattr(paper, "dois", ""),
                "reborn_doi": getattr(paper, "reborn_doi", ""),
                "authors": authors,
                "concepts": concepts,
                "research_fields": research_fields,
                "scientific_venue": journal_conference,
                "publisher": publisher,
                "reborn_date": localtime(paper.created_at).strftime("%B %d, %Y")
                if hasattr(paper, "created_at") and paper.created_at
                else None,
            }
            statements = []
            for statement in paper.statements.all().order_by("order"):
                has_part = statement.has_part_statements.first()
                authors = []
                for author in statement.authors.all():
                    authors.append(
                        {
                            "name": author.label,
                            "author_id": author.author_id,
                            "orcid": author._id
                            if author._id.startswith("https://orcid.org/")
                            else None,
                        }
                    )

                concepts = []
                for concept in statement.concepts.all():
                    concepts.append(
                        {
                            "label": concept.label,
                            "concept_id": concept.concept_id,
                            "see_also": concept.see_also,
                        }
                    )
                statements.append(
                    {
                        "statement_id": statement.statement_id,
                        "label": statement.label,
                        "authors": authors,
                        "concepts": concepts,
                        "type": {
                            "name": has_part.schema_type.name,
                            "description": has_part.schema_type.description,
                            "type_id": has_part.schema_type.type_id,
                            "properties": [
                                s.split("#", 1)[1] if "#" in s else ""
                                for s in has_part.schema_type.property
                            ],
                        },
                    }
                )
            # Create serializable paper dictionary

            serialized_papers.append(
                {
                    "article": paper_dict,
                    "statements": statements,
                }
            )

        total_pages = (total + query_filter.per_page - 1) // query_filter.per_page
        has_next = query_filter.page < total_pages
        has_previous = query_filter.page > 1

        return Response(
            {
                "results": serialized_papers,
                "total_count": total,
                "page": query_filter.page,
                "page_size": query_filter.per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            }
        )

        # except Exception as e:
        #     logger.error(f"Error in query_data: {str(e)}")
        #     return CommonResponseDTO(
        #         success=False, message=f"Failed to query data: {str(e)}"
        #     )

    def statement_data_type(self, statement: str) -> any:
        data_type = []
        components = []
        print("-----statement.components.all()-------")
        for component in statement.components.all():
            units = []
            for unit in component.units.all():
                units.append(
                    {
                        "label": unit.label,
                        "type": unit.type,
                        "exact_match": unit.exact_match,
                        "close_match": unit.close_match,
                    }
                )
            properties = []
            for property in component.properties.all():
                properties.append(
                    {
                        "label": property.label,
                        "exact_match": property.exact_match,
                        "close_match": property.close_match,
                    }
                )
            matrices = []
            for matrix in component.matrices.all():
                matrices.append(
                    {
                        "label": matrix.label,
                        "type": matrix.type,
                        "exact_match": matrix.exact_match,
                        "close_match": matrix.close_match,
                    }
                )
            object_of_interests = []
            for object_of_interest in component.object_of_interests.all():
                object_of_interests.append(
                    {
                        "label": object_of_interest.label,
                        "type": object_of_interest.type,
                        "exact_match": object_of_interest.exact_match,
                        "close_match": object_of_interest.close_match,
                    }
                )
            components.append(
                {
                    "string_match": component.string_match,
                    "exact_match": component.exact_match,
                    "close_match": component.close_match,
                    "label": component.label,
                    "type": component.type,
                    "units": units,
                    "properties": properties,
                    "matrices": matrices,
                    "object_of_interests": object_of_interests,
                }
            )
        implement_statements = statement.implement_statements.all()
        implements = []
        for implement_statement in implement_statements:
            implements.append(
                f"{os.environ.get('DOMAIN_NAME', 'https://reborn.orkg.org')}{implement_statement.source_code.url}"
                if implement_statement.source_code
                else implement_statement.url
            )
        for data_type_statement in statement.data_type_statement.all():
            executes = []
            for software_method in data_type_statement.executes.all():
                if software_method:
                    execute_part_ofs = software_method.part_of.all()
                    software_libraries = []
                    for software_library in execute_part_ofs:
                        software = software_library.part_of
                        software_libraries.append(
                            {
                                "label": software_library.label,
                                "version_info": software_library.version_info,
                                "has_support_url": software_library.has_support_url,
                                "part_of": {
                                    "label": software.label,
                                    "version_info": software.version_info,
                                    "has_support_url": software.has_support_url,
                                },
                            }
                        )
                    executes.append(
                        {
                            "part_of": software_libraries,
                            "label": software_method.label,
                            "is_implemented_by": software_method.is_implemented_by,
                            "has_support_url": software_method.has_support_url,
                        }
                    )
            has_inputs = []
            for has_input in data_type_statement.has_inputs.all():
                has_characteristic = None
                if has_input.has_characteristic:
                    has_characteristic = {
                        "number_rows": has_input.has_characteristic.number_rows,
                        "number_columns": has_input.has_characteristic.number_columns,
                    }
                has_expressions = []
                for has_expression in has_input.has_expression.all():
                    has_expressions.append(
                        {
                            "label": has_expression.label,
                            "source_url": f"{os.environ.get('DOMAIN_NAME', 'https://reborn.orkg.org')}{has_expression.source_image.url}"
                            if has_expression.source_image
                            else has_expression.source_url,
                        }
                    )
                has_parts = []
                for has_part in has_input.has_part.all():
                    has_parts.append(
                        {
                            "label": has_part.label,
                            "see_also": has_part.see_also,
                        }
                    )
                has_inputs.append(
                    {
                        "label": has_input.label,
                        "source_url": f"{os.environ.get('DOMAIN_NAME', 'https://reborn.orkg.org')}{has_input.source_file.url}"
                        if has_input.source_file
                        else has_input.source_url,
                        "comment": has_input.comment,
                        "source_table": has_input.source_table,
                        "has_characteristic": has_characteristic,
                        "has_expressions": has_expressions,
                        "has_parts": has_parts,
                    }
                )
            has_outputs = []
            for has_output in data_type_statement.has_outputs.all():
                has_characteristic = None
                if has_output.has_characteristic:
                    has_characteristic = {
                        "number_rows": has_output.has_characteristic.number_rows,
                        "number_columns": has_output.has_characteristic.number_columns,
                    }
                has_expressions = []
                for has_expression in has_output.has_expression.all():
                    has_expressions.append(
                        {
                            "label": has_expression.label,
                            "source_url": f"{os.environ.get('DOMAIN_NAME', 'https://reborn.orkg.org')}{has_expression.source_image.url}"
                            if has_expression.source_image
                            else has_expression.source_url,
                        }
                    )
                has_parts = []
                for has_part in has_output.has_part.all():
                    has_parts.append(
                        {
                            "label": has_part.label,
                            "see_also": has_part.see_also,
                        }
                    )
                has_outputs.append(
                    {
                        "label": has_output.label,
                        "source_url": f"{os.environ.get('DOMAIN_NAME', 'https://reborn.orkg.org')}{has_output.source_file.url}"
                        if has_output.source_file
                        else has_output.source_url,
                        "comment": has_output.comment,
                        "source_table": has_output.source_table,
                        "has_characteristic": has_characteristic,
                        "has_expressions": has_expressions,
                        "has_parts": has_parts,
                    }
                )
            dt = {
                "label": data_type_statement.label,
                "type": data_type_statement.type,
                "see_also": data_type_statement.see_also,
                "executes": executes,
                "has_input": has_inputs,
                "has_output": has_outputs,
            }
            if data_type_statement.type == "AlgorithmEvaluation":
                if data_type_statement.evaluate:
                    dt["evaluates"] = {
                        "label": data_type_statement.evaluate.label,
                        "type": data_type_statement.evaluate.type,
                        # "see_also": data_type_statement.evaluate.see_also
                        # if data_type_statement.evaluate.see_also[0] is not None
                        # else [],
                        "see_also": data_type_statement.evaluate.see_also,
                    }
                if data_type_statement.evaluates_for:
                    dt["evaluates_for"] = {
                        "label": data_type_statement.evaluates_for.label,
                        "type": data_type_statement.evaluates_for.type,
                        "see_also": data_type_statement.evaluates_for.see_also,
                    }
            if data_type_statement.type == "MultilevelAnalysis":
                targets = []
                for target in data_type_statement.targets.all():
                    targets.append(
                        {
                            "label": target.label,
                            "type": target.type,
                            "see_also": target.see_also,
                        }
                    )
                if targets:
                    dt["targets"] = targets
                levels = []
                for level in data_type_statement.level.all():
                    levels.append(
                        {
                            "label": level.label,
                            "type": level.type,
                            "see_also": level.see_also,
                        }
                    )
                if levels:
                    dt["level"] = levels
            if data_type_statement.type == "GroupComparison":
                targets = []
                for target in data_type_statement.targets.all():
                    targets.append(
                        {
                            "label": target.label,
                            "type": target.type,
                            "see_also": target.see_also,
                        }
                    )
                if targets:
                    dt["targets"] = targets
            has_part = statement.has_part_statements.first()
            data_type.append(
                {
                    "has_part": dt,
                    "is_implemented_by": implements,
                    "components": components,
                    "type": {
                        "name": data_type_statement.schema_type.name,
                        "description": data_type_statement.schema_type.description,
                        "type_id": data_type_statement.schema_type.type_id,
                        "properties": [
                            s.split("#", 1)[1] if "#" in s else ""
                            for s in data_type_statement.schema_type.property
                        ],
                    },
                }
            )
        return data_type

    def get_statement(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement with related data."""
        print("-------------------get_statement-----------------", __file__)
        try:
            statement = self.statement_repository.find_by_id(statement_id)
            authors = []
            for author in statement.authors.all():
                authors.append({"label": author.label, "author_id": author.author_id})

            concepts = []
            for concept in statement.concepts.all():
                concepts.append(
                    {"label": concept.label, "concept_id": concept.concept_id}
                )
            data_type = []
            if statement_id == statement.statement_id:
                data_type = self.statement_data_type(statement)
            result = CommonResponseDTO(
                success=True,
                result={
                    "data_type": data_type,
                },
                total_count=1,
            )
            return result

        except Exception as e:
            logger.error(f"Error in get_statement: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve statement: {str(e)}"
            )

    def get_article_statement(self, statement_id: str) -> CommonResponseDTO:
        """Get a statement by its ID."""
        try:
            statement_in_paper = (
                self.statement_repository.find_paper_with_statement_details(
                    statement_id
                )
            )
            print("------------get_statement_by_id-----------statement---------------")
            paper = None
            if statement_in_paper:
                paper = self.paper_repository.find_by_id(statement_in_paper.article_id)
            if paper:
                paper_dto = self._map_paper_to_dto(paper)
                authors = []
                for author in paper_dto.authors:
                    authors.append(
                        {
                            "label": author.label,
                            "orcid": author.orcid,
                            "author_id": author.author_id,
                        }
                    )
                concepts = []
                if paper_dto.concepts:
                    for concept in paper_dto.concepts:
                        concepts.append(
                            {
                                "label": concept.label,
                                "concept_id": concept.id,
                            }
                        )
                paper_info = {
                    "name": paper_dto.name,
                    "article_id": paper_dto.article_id,
                    "authors": authors,
                    "abstract": paper_dto.abstract,
                    "dois": paper_dto.dois,
                    "reborn_doi": paper_dto.reborn_doi,
                    "scientific_venue": paper_dto.journal
                    if paper_dto.journal
                    else paper_dto.conference,
                    "concepts": concepts,
                    "research_fields": paper_dto.research_fields,
                    "publisher": paper_dto.publisher,
                    "reborn_date": localtime(paper_dto.created_at).strftime(
                        "%B %d, %Y"
                    ),
                    "date_published": localtime(paper_dto.date_published).strftime(
                        "%Y"
                    ),
                }
                statements = []
                for statement in paper.statements.all().order_by("order"):
                    has_part = statement.has_part_statements.first()
                    authors = []
                    for author in statement.authors.all():
                        authors.append(
                            {
                                "name": author.label,
                                "author_id": author.author_id,
                                "orcid": author._id
                                if author._id.startswith("https://orcid.org/")
                                else None,
                            }
                        )

                    concepts = []
                    for concept in statement.concepts.all():
                        concepts.append(
                            {
                                "label": concept.label,
                                "concept_id": concept.concept_id,
                                "see_also": concept.see_also,
                            }
                        )
                    data_type = {}
                    if statement_id == statement.statement_id:
                        data_type = self.statement_data_type(statement)
                    statements.append(
                        {
                            "statement_id": statement.statement_id,
                            "label": statement.label,
                            "authors": authors,
                            "concepts": concepts,
                            "data_type": data_type,
                            "type": {
                                "name": has_part.schema_type.name,
                                "description": has_part.schema_type.description,
                                "type_id": has_part.schema_type.type_id,
                                "properties": [
                                    s.split("#", 1)[1] if "#" in s else ""
                                    for s in has_part.schema_type.property
                                ],
                            },
                        }
                    )
                result = CommonResponseDTO(
                    success=True,
                    result={
                        "article": paper_info,
                        "statements": statements,
                    },
                    total_count=len(statements),
                )
                return result

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            # return result

            return CommonResponseDTO(
                success=False, message=f"Paper with ID {statement_id} not found"
            )

        except Exception as e:
            logger.error(f"Error in get_paper_by_id: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve paper: {str(e)}"
            )

    def get_paper_by_id(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper by its ID."""
        # cache_key = f"paper_{paper_id}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result
        print("-----------get_paper_by_id--------------", __file__)
        try:
            paper = self.paper_repository.find_by_id(paper_id)
            if paper:
                paper_dto = self._map_paper_to_dto(paper)
                authors = []
                for author in paper_dto.authors:
                    authors.append(
                        {
                            "label": author.label,
                            "orcid": author.orcid,
                            "author_id": author.author_id,
                        }
                    )
                concepts = []
                if paper_dto.concepts:
                    for concept in paper_dto.concepts:
                        concepts.append(
                            {
                                "label": concept.label,
                                "concept_id": concept.id,
                            }
                        )
                paper_info = {
                    "name": paper_dto.name,
                    "article_id": paper_dto.article_id,
                    "authors": authors,
                    "abstract": paper_dto.abstract,
                    "dois": paper_dto.dois,
                    "reborn_doi": paper_dto.reborn_doi,
                    "scientific_venue": paper_dto.journal
                    if paper_dto.journal
                    else paper_dto.conference,
                    "concepts": concepts,
                    "research_fields": paper_dto.research_fields,
                    "publisher": paper_dto.publisher,
                    "reborn_date": localtime(paper_dto.created_at).strftime(
                        "%B %d, %Y"
                    ),
                    "date_published": localtime(paper_dto.date_published).strftime(
                        "%Y"
                    ),
                }
                statements = []
                for statement in paper.statements.all().order_by("order"):
                    has_part = statement.has_part_statements.first()
                    authors = []
                    for author in statement.authors.all():
                        authors.append(
                            {
                                "name": author.label,
                                "author_id": author.author_id,
                                "orcid": author._id
                                if author._id.startswith("https://orcid.org/")
                                else None,
                            }
                        )

                    concepts = []
                    for concept in statement.concepts.all():
                        concepts.append(
                            {
                                "label": concept.label,
                                "concept_id": concept.concept_id,
                                "definition": concept.definition,
                                "see_also": concept.see_also,
                            }
                        )

                    statements.append(
                        {
                            "statement_id": statement.statement_id,
                            "label": statement.label,
                            "authors": authors,
                            "concepts": concepts,
                            "type": {
                                "name": has_part.schema_type.name,
                                "description": has_part.schema_type.description,
                                "type_id": has_part.schema_type.type_id,
                                "properties": [
                                    s.split("#", 1)[1] if "#" in s else ""
                                    for s in has_part.schema_type.property
                                ],
                            },
                        }
                    )
                result = CommonResponseDTO(
                    success=True,
                    result={
                        "article": paper_info,
                        "statements": statements,
                    },
                    total_count=len(statements),
                )
                return result

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            # return result

            return CommonResponseDTO(
                success=False, message=f"Paper with ID {paper_id} not found"
            )

        except Exception as e:
            logger.error(f"Error in get_paper_by_id: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve paper: {str(e)}"
            )

    def get_authors(self, search_term: str) -> List[AuthorOutputDTO]:
        """Get authors by search term."""
        try:
            authors = self.author_repository.find_by_name(search_term)
            return [
                AuthorOutputDTO(
                    id=author.id,
                    given_name=author.given_name,
                    family_name=author.family_name,
                    label=author.label or f"{author.given_name} {author.family_name}",
                )
                for author in authors
            ]

        except Exception as e:
            logger.error(f"Error in get_authors: {str(e)}")
            return []

    def get_concepts(self, search_term: str) -> List[ConceptOutputDTO]:
        """Get concepts by search term."""
        try:
            concepts = self.concept_repository.find_by_label(search_term)
            return [
                ConceptOutputDTO(
                    id=concept.id, label=concept.label, identifier=concept.identifier
                )
                for concept in concepts
            ]

        except Exception as e:
            logger.error(f"Error in get_concepts: {str(e)}")
            return []

    def get_latest_concepts(self) -> List[ConceptOutputDTO]:
        """Get latest concepts."""
        try:
            concepts = self.concept_repository.get_latest_concepts()
            return [
                ConceptOutputDTO(
                    id=concept.id, label=concept.label, identifier=concept.identifier
                )
                for concept in concepts
            ]

        except Exception as e:
            logger.error(f"Error in get_latest_concepts: {str(e)}")
            return []

    def get_titles(self, search_term: str) -> List[Dict[str, Any]]:
        """Get paper titles by search term."""
        try:
            papers = self.paper_repository.search_by_title(search_term)
            return [{"id": paper.id, "name": paper.title} for paper in papers]

        except Exception as e:
            logger.error(f"Error in get_titles: {str(e)}")
            return []

    def get_journals(self, search_term: str) -> List[Dict[str, Any]]:
        """Get journals by search term."""
        try:
            journals = self.journal_repository.find_by_name(search_term)
            return [
                {"id": journal.get("_id", ""), "name": journal.get("label", "")}
                for journal in journals
            ]

        except Exception as e:
            logger.error(f"Error in get_journals: {str(e)}")
            return []

    def get_research_fields(self, search_term: str) -> List[Dict[str, Any]]:
        """Get research fields by search term."""
        try:
            research_fields = self.research_field_repository.find_by_label(search_term)
            print("---------research_fields----------")
            return [
                {
                    "research_field_id": rf.research_field_id,
                    "related_identifier": rf.related_identifier,
                    "label": rf.label,
                }
                for rf in research_fields
            ]

        except Exception as e:
            logger.error(f"Error in get_research_fields: {str(e)}")
            return []

    def get_paper(self, paper_id: str) -> CommonResponseDTO:
        """Get a paper with related data."""
        try:
            paper = self.paper_repository.find_by_id(paper_id)
            print("-----------get_paper--------------", __file__)
            # Group statements by article ID
            grouped_data = {}
            if paper:
                # Get statements for this paper
                statements = self.statement_repository.find_by_paper_id(paper.id)
                paper_dto = self._map_paper_to_dto(paper)

                for statement in statements:
                    statement_dto = self._map_statement_to_dto(statement)
                    paper_dto.statements.append(statement_dto)

                grouped_data[paper.id] = paper_dto

            return CommonResponseDTO(
                success=True, result=grouped_data, total_count=len(grouped_data)
            )

        except Exception as e:
            logger.error(f"Error in get_paper: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to retrieve paper: {str(e)}"
            )

    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
    ) -> PaginatedResponseDTO:
        """Get latest statements with filters."""
        # cache_key = f"latest_statements_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result
        print("------------get_latest_statements-----------", __file__)
        # try:
        statements, total = self.statement_repository.get_latest_statements(
            research_fields=research_fields,
            search_query=search_query,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
            search_type=search_type,
        )

        result = PaginatedResponseDTO(
            content=[self._map_statement_to_dto(statement) for statement in statements],
            total_elements=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size),
        )

        # Cache for 15 minutes
        # cache.set(cache_key, result, settings.CACHE_TTL)
        return result

        # except Exception as e:
        #     logger.error(f"Error in get_latest_statements: {str(e)}")
        #     raise DatabaseError(f"Failed to retrieve latest statements: {str(e)}")

    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
        search_type: str = "keyword",
    ) -> PaginatedResponseDTO:
        """Get latest articles with filters."""
        print("-------------get_latest_articles---------------", __file__)
        # cache_key = f"latest_articles_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            papers, total = self.paper_repository.get_latest_articles(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
                search_type=search_type,
            )
            result = PaginatedResponseDTO(
                content=[self._map_paper_to_dto(paper) for paper in papers],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest articles: {str(e)}")

    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest keywords with filters."""
        # cache_key = f"latest_keywords_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            concepts, total = self.concept_repository.get_latest_keywords(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[
                    ConceptOutputDTO(
                        id=concept.id,
                        label=concept.label,
                        identifier=concept.identifier,
                    )
                    for concept in concepts
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_keywords: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest keywords: {str(e)}")

    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest authors with filters."""
        # cache_key = f"latest_authors_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result
        print("-------------get_latest_authors----------", __file__)
        try:
            authors, total = self.author_repository.get_latest_authors(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )

            result = PaginatedResponseDTO(
                content=[
                    ShortAuthorOutputDTO(
                        label=author.label,
                        author_id=author.author_id,
                        orcid=author.orcid
                        if author.orcid and author.orcid.startswith("https://orcid.org")
                        else None,
                    )
                    for author in authors
                ],
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_authors: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest authors: {str(e)}")

    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedResponseDTO:
        """Get latest journals with filters."""
        print("-------------get_latest_journals----------", __file__)
        # cache_key = f"latest_journals_{research_fields}_{search_query}_{sort_order}_{page}_{page_size}"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            journals, total = self.journal_repository.get_latest_journals(
                research_fields=research_fields,
                search_query=search_query,
                sort_order=sort_order,
                page=page,
                page_size=page_size,
            )
            # print(journals)
            content = []
            for journal in journals:
                if isinstance(journal, dict):
                    content.append(
                        {
                            "journal_id": journal.get("journal_conference_id", ""),
                            "name": journal.get("label", ""),
                            "publisher": journal.get("publisher", {}).label
                            if journal.get("publisher")
                            else "",
                        }
                    )
            result = PaginatedResponseDTO(
                content=content,
                total_elements=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size),
            )

            # Cache for 15 minutes
            # cache.set(cache_key, result, settings.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest journals: {str(e)}")

    def extract_paper(self, url_dto: ScraperUrlInputDTO) -> CommonResponseDTO:
        # """Extract a paper from a URL."""
        try:
            url = str(url_dto.url)
            self.scraper.set_url(url)
            json_files = self.scraper.all_json_files()
            ro_crate = self.scraper.load_json_from_url(
                json_files["ro-crate-metadata.json"]
            )
            self.paper_repository.add_article(ro_crate, json_files)
            # Invalidate relevant caches
            # cache.delete_pattern("all_papers_*")
            # cache.delete_pattern("latest_articles_*")

            return CommonResponseDTO(
                success=True, message="Paper extracted and saved successfully"
            )

        except Exception as e:
            logger.error(f"Error in extract_paper: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to extract paper ssss: {str(e)}"
            )

    def delete_database(self) -> CommonResponseDTO:
        """Delete the database."""
        try:
            success = self.paper_repository.delete_database()

            # Clear all caches
            cache.clear()

            return CommonResponseDTO(
                success=success,
                message="Database deleted successfully"
                if success
                else "Failed to delete database",
            )

        except Exception as e:
            logger.error(f"Error in delete_database: {str(e)}")
            return CommonResponseDTO(
                success=False, message=f"Failed to delete database: {str(e)}"
            )

    def _map_paper_to_dto(self, paper) -> ShortPaperOutputDTO:
        """Map a paper entity to its DTO."""
        authors = []
        # print("----------_map_paper_to_dto------------", __file__)
        for author in paper.authors:
            if isinstance(author, dict):
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.get("label", ""),
                        family_name=author.get("family_name", ""),
                        orcid=author.get("orcid", ""),
                        author_id=author.get("author_id", ""),
                    )
                )
            else:
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.label,
                        family_name=author.family_name,
                        orcid=author.orcid,
                        author_id=author.author_id,
                    )
                )
        research_fields = []
        if paper.research_fields:
            for research_field in paper.research_fields:
                research_fields.append(
                    {
                        "label": research_field.label,
                        "research_field_id": research_field.research_field_id,
                        "related_identifier": research_field.related_identifier,
                    }
                )
        scientific_venue = None
        if paper.journal:
            journal = paper.journal
            scientific_venue = {
                "label": journal.label,
                "id": journal.journal_conference_id,
                "identifier": journal._id,
            }

        return ShortPaperOutputDTO(
            id=paper.id,
            article_id=paper.article_id,
            name=paper.name,
            concepts=paper.concepts,
            research_fields=research_fields,
            reborn_doi=paper.reborn_doi,
            dois=paper.dois,
            abstract=paper.abstract,
            publisher=paper.publisher.label,
            authors=authors,
            journal=scientific_venue,
            date_published=paper.date_published,
        )

    def _map_statement_to_dto(self, statement) -> StatementOutputDTO:
        """Map a statement entity to its DTO."""
        authors = []
        for author in statement.author:
            if isinstance(author, dict):
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.label,
                    )
                )
            else:
                authors.append(
                    ShortAuthorOutputDTO(
                        label=author.label,
                    )
                )

        return ShortStatementOutputDTO(
            id=statement.id,
            statement_id=statement.statement_id,
            authors=authors,
            article_id=statement.article_id,
            article_name=statement.article_name,
            date_published=statement.date_published,
            journal_conference=statement.journal_conference,
            label=statement.label,
            created_at=statement.created_at,
            updated_at=statement.updated_at,
        )
