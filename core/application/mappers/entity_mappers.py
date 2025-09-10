"""
Entity mappers for the REBORN API.

These mappers convert between domain entities and DTOs.
"""

from typing import List, Dict, Any, Optional, cast
from datetime import datetime

from core.domain.entities import (
    Article,
    Statement,
    Author,
    Concept,
    ResearchField,
    Journal,
    Conference,
    Notation,
    Contribution,
)
from core.application.dtos.input_dtos import (
    PaperInputDTO,
    StatementInputDTO,
    AuthorInputDTO,
    ConceptInputDTO,
    ResearchFieldInputDTO,
    ContributionInputDTO,
)
from core.application.dtos.output_dtos import (
    PaperOutputDTO,
    StatementOutputDTO,
    AuthorOutputDTO,
    ConceptOutputDTO,
    ResearchFieldOutputDTO,
    JournalOutputDTO,
    ConferenceOutputDTO,
    NotationOutputDTO,
    ContributionOutputDTO,
)


class AuthorMapper:
    """Mapper for Author entities."""

    @staticmethod
    def to_entity(dto: AuthorInputDTO) -> Author:
        """Convert DTO to entity."""
        return Author(
            id=dto.id or "",
            given_name=dto.given_name,
            family_name=dto.family_name,
            label=dto.label,
        )

    @staticmethod
    def to_dto(entity: Author) -> AuthorOutputDTO:
        """Convert entity to DTO."""
        return AuthorOutputDTO(
            id=entity.id,
            given_name=entity.given_name,
            family_name=entity.family_name,
            label=entity.label or f"{entity.given_name} {entity.family_name}",
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Author:
        """Convert dictionary to entity."""
        return Author(
            id=data.get("id", "") or data.get("@id", ""),
            given_name=data.get("given_name", "") or data.get("givenName", ""),
            family_name=data.get("family_name", "") or data.get("familyName", ""),
            label=data.get("label", ""),
        )


class ConceptMapper:
    """Mapper for Concept entities."""

    @staticmethod
    def to_entity(dto: ConceptInputDTO) -> Concept:
        """Convert DTO to entity."""
        return Concept(id=dto.id or "", label=dto.label, identifier=dto.identifier)

    @staticmethod
    def to_dto(entity: Concept) -> ConceptOutputDTO:
        """Convert entity to DTO."""
        return ConceptOutputDTO(
            id=entity.id, label=entity.label, identifier=entity.identifier
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Concept:
        """Convert dictionary to entity."""
        return Concept(
            id=data.get("id", "") or data.get("@id", ""),
            label=data.get("label", ""),
            identifier=data.get("identifier", ""),
        )


class ResearchFieldMapper:
    """Mapper for ResearchField entities."""

    @staticmethod
    def to_entity(dto: ResearchFieldInputDTO) -> ResearchField:
        """Convert DTO to entity."""
        return ResearchField(id=dto.id or "", label=dto.label)

    @staticmethod
    def to_dto(entity: ResearchField) -> ResearchFieldOutputDTO:
        """Convert entity to DTO."""
        return ResearchFieldOutputDTO(id=entity.id, label=entity.label)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ResearchField:
        """Convert dictionary to entity."""
        return ResearchField(
            id=data.get("id", "") or data.get("@id", ""), label=data.get("label", "")
        )


class JournalMapper:
    """Mapper for Journal entities."""

    @staticmethod
    def to_dto(entity: Journal) -> JournalOutputDTO:
        """Convert entity to DTO."""
        return JournalOutputDTO(
            id=entity.id, label=entity.label, publisher=entity.publisher
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Journal:
        """Convert dictionary to entity."""
        return Journal(
            id=data.get("id", "") or data.get("@id", ""),
            label=data.get("label", ""),
            publisher=data.get("publisher", {}),
        )


class ConferenceMapper:
    """Mapper for Conference entities."""

    @staticmethod
    def to_dto(entity: Conference) -> ConferenceOutputDTO:
        """Convert entity to DTO."""
        return ConferenceOutputDTO(
            id=entity.id, label=entity.label, publisher=entity.publisher
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Conference:
        """Convert dictionary to entity."""
        return Conference(
            id=data.get("id", "") or data.get("@id", ""),
            label=data.get("label", ""),
            publisher=data.get("publisher", {}),
        )


class NotationMapper:
    """Mapper for Notation entities."""

    @staticmethod
    def to_dto(entity: Notation) -> NotationOutputDTO:
        """Convert entity to DTO."""
        concept_dto = None
        if entity.concept:
            concept_dto = ConceptMapper.to_dto(entity.concept)

        return NotationOutputDTO(id=entity.id, label=entity.label, concept=concept_dto)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Notation:
        """Convert dictionary to entity."""
        concept = None
        if "concept" in data and data["concept"]:
            concept = ConceptMapper.from_dict(data["concept"])

        return Notation(
            id=data.get("id", "") or data.get("@id", ""),
            label=data.get("label", ""),
            concept=concept,
        )


class ContributionMapper:
    """Mapper for Contribution entities."""

    @staticmethod
    def to_entity(dto: ContributionInputDTO) -> Contribution:
        """Convert DTO to entity."""
        authors = [AuthorMapper.to_entity(author_dto) for author_dto in dto.author]

        return Contribution(
            id=dto.id or "",
            title=dto.title,
            author=authors,
            info=dto.info,
            paper_id=dto.paper_id,
            json_id=dto.json_id,
            json_type=dto.json_type,
            json_context=dto.json_context,
            predicates=dto.predicates or {},
        )

    @staticmethod
    def to_dto(entity: Contribution) -> ContributionOutputDTO:
        """Convert entity to DTO."""
        authors = [AuthorMapper.to_dto(author) for author in entity.author]

        return ContributionOutputDTO(
            id=entity.id,
            title=entity.title,
            author=authors,
            info=entity.info,
            paper_id=entity.paper_id,
            json_id=entity.json_id,
            json_type=entity.json_type,
            json_context=entity.json_context,
            predicates=entity.predicates or {},
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Contribution:
        """Convert dictionary to entity."""
        authors = []
        if "author" in data and data["author"]:
            authors = [AuthorMapper.from_dict(author) for author in data["author"]]

        return Contribution(
            id=data.get("id", "") or data.get("_id", ""),
            title=data.get("title", ""),
            author=authors,
            info=data.get("info", {}),
            paper_id=data.get("paper_id", None),
            json_id=data.get("json_id", None),
            json_type=data.get("json_type", None),
            json_context=data.get("json_context", None),
            predicates=data.get("predicates", {}),
        )


class StatementMapper:
    """Mapper for Statement entities."""

    @staticmethod
    def to_entity(dto: StatementInputDTO) -> Statement:
        """Convert DTO to entity."""
        authors = [AuthorMapper.to_entity(author_dto) for author_dto in dto.author]
        notation = None
        if dto.notation:
            concept = None
            if dto.notation.concept:
                concept = ConceptMapper.to_entity(dto.notation.concept)

            notation = Notation(
                id=dto.notation.id or "", label=dto.notation.label, concept=concept
            )

        return Statement(
            id=dto.id or "",
            content=dto.content,
            author=authors,
            article_id=dto.article_id,
            supports=dto.supports,
            notation=notation,
            statement_id=dto.statement_id,
        )

    @staticmethod
    def to_dto(entity: Statement) -> StatementOutputDTO:
        """Convert entity to DTO."""
        authors = [AuthorMapper.to_dto(author) for author in entity.author]
        notation = None
        if entity.notation:
            notation = NotationMapper.to_dto(entity.notation)

        return StatementOutputDTO(
            id=entity.id,
            statement_id=entity.statement_id or entity.id,
            content=entity.content,
            author=authors,
            article_id=entity.article_id,
            supports=entity.supports,
            notation=notation,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Statement:
        """Convert dictionary to entity."""
        authors = []
        if "author" in data and data["author"]:
            if isinstance(data["author"], list):
                authors = [AuthorMapper.from_dict(author) for author in data["author"]]
            else:
                authors = [AuthorMapper.from_dict(data["author"])]

        notation = None
        if "notation" in data and data["notation"]:
            notation = NotationMapper.from_dict(data["notation"])

        supports = data.get("supports", [])
        if not isinstance(supports, list):
            supports = [supports] if supports else []

        created_at = None
        if "created_at" in data and data["created_at"]:
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            else:
                created_at = data["created_at"]

        updated_at = None
        if "updated_at" in data and data["updated_at"]:
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(
                    data["updated_at"].replace("Z", "+00:00")
                )
            else:
                updated_at = data["updated_at"]

        return Statement(
            id=data.get("id", "") or data.get("_id", ""),
            content=data.get("content", {}),
            author=authors,
            article_id=data.get("article_id", ""),
            supports=supports,
            notation=notation,
            statement_id=data.get("statement_id", None),
            created_at=created_at,
            updated_at=updated_at,
        )


class PaperMapper:
    """Mapper for Paper entities."""

    @staticmethod
    def to_entity(dto: PaperInputDTO) -> Article:
        """Convert DTO to entity."""
        authors = [AuthorMapper.to_entity(author_dto) for author_dto in dto.author]
        research_fields = []
        if dto.research_fields:
            research_fields = [
                ResearchFieldMapper.to_entity(rf_dto) for rf_dto in dto.research_fields
            ]

        return Article(
            id=dto.id or "",
            title=dto.title,
            author=authors,
            abstract=dto.abstract,
            contributions=[],  # Will be filled separately
            statements=[],  # Will be filled separately
            dois=dto.dois,
            date_published=dto.date_published,
            entity=dto.entity,
            external=str(dto.external) if dto.external else None,
            info=dto.info or {},
            timeline={},
            journal=None,  # Will be filled separately
            conference=None,  # Will be filled separately
            publisher=dto.publisher,
            research_fields=research_fields,
            research_fields_id=[rf.id for rf in research_fields],
            article_id=dto.article_id,
            reborn_doi=None,
            paper_type=dto.paper_type,
            concepts=[],  # Will be filled separately
        )

    @staticmethod
    def to_dto(entity: Article) -> PaperOutputDTO:
        """Convert entity to DTO."""
        authors = [AuthorMapper.to_dto(author) for author in entity.author]
        research_fields = [
            ResearchFieldMapper.to_dto(rf) for rf in entity.research_fields
        ]
        contributions = [
            ContributionMapper.to_dto(contribution)
            for contribution in entity.contributions
        ]
        statements = [
            StatementMapper.to_dto(statement) for statement in entity.statements
        ]
        concepts = [ConceptMapper.to_dto(concept) for concept in entity.concepts]
        journal = None
        if entity.journal:
            journal = JournalMapper.to_dto(entity.journal)

        conference = None
        if entity.conference:
            conference = ConferenceMapper.to_dto(entity.conference)

        return PaperOutputDTO(
            id=entity.id,
            article_id=entity.article_id,
            title=entity.title,
            author=authors,
            abstract=entity.abstract,
            contributions=contributions,
            statements=statements,
            dois=entity.dois,
            date_published=entity.date_published,
            entity=entity.entity,
            external=entity.external,
            info=entity.info or {},
            timeline=entity.timeline or {},
            journal=journal,
            conference=conference,
            publisher=entity.publisher,
            research_fields=research_fields,
            reborn_doi=entity.reborn_doi,
            paper_type=entity.paper_type,
            concepts=concepts,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Article:
        """Convert dictionary to entity."""
        # Process authors
        authors = []
        if "author" in data and data["author"]:
            if isinstance(data["author"], list):
                authors = [AuthorMapper.from_dict(author) for author in data["author"]]
            else:
                authors = [AuthorMapper.from_dict(data["author"])]

        # Process research fields
        research_fields = []
        research_fields_id = []
        if "research_fields" in data and data["research_fields"]:
            if isinstance(data["research_fields"], list):
                research_fields = [
                    ResearchFieldMapper.from_dict(rf) for rf in data["research_fields"]
                ]
                research_fields_id = [rf.id for rf in research_fields]

        # Process contributions
        contributions = []
        if "contributions" in data and data["contributions"]:
            if isinstance(data["contributions"], list):
                contributions = [
                    ContributionMapper.from_dict(contribution)
                    for contribution in data["contributions"]
                ]
            elif isinstance(data["contributions"], dict):
                # Handle the case where contributions is a dict
                contributions = [
                    ContributionMapper.from_dict({"id": k, **v})
                    for k, v in data["contributions"].items()
                ]

        # Process statements
        statements = []
        if "statements" in data and data["statements"]:
            if isinstance(data["statements"], list):
                statements = [
                    StatementMapper.from_dict(statement)
                    for statement in data["statements"]
                ]

        # Process journal
        journal = None
        if "journal" in data and data["journal"]:
            journal = JournalMapper.from_dict(data["journal"])

        # Process conference
        conference = None
        if "conference" in data and data["conference"]:
            conference = ConferenceMapper.from_dict(data["conference"])

        # Process concepts
        concepts = []
        if "concepts" in data and data["concepts"]:
            if isinstance(data["concepts"], list):
                concepts = [
                    ConceptMapper.from_dict(concept) for concept in data["concepts"]
                ]

        # Process dates
        created_at = None
        if "created_at" in data and data["created_at"]:
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            else:
                created_at = data["created_at"]

        updated_at = None
        if "updated_at" in data and data["updated_at"]:
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(
                    data["updated_at"].replace("Z", "+00:00")
                )
            else:
                updated_at = data["updated_at"]

        date_published = None
        if "date_published" in data and data["date_published"]:
            if isinstance(data["date_published"], str):
                try:
                    date_published = datetime.fromisoformat(
                        data["date_published"].replace("Z", "+00:00")
                    )
                except ValueError:
                    # Try other format
                    try:
                        date_published = datetime.strptime(
                            data["date_published"], "%Y-%m-%d"
                        )
                    except ValueError:
                        pass
            else:
                date_published = data["date_published"]

        return Article(
            id=data.get("id", "") or data.get("_id", ""),
            title=data.get("title", "") or data.get("name", ""),
            author=authors,
            abstract=data.get("abstract", ""),
            contributions=contributions,
            statements=statements,
            dois=data.get("dois", None),
            date_published=date_published,
            entity=data.get("entity", None),
            external=data.get("external", None),
            info=data.get("info", {}) or {},
            timeline=data.get("timeline", {}) or {},
            journal=journal,
            conference=conference,
            publisher=data.get("publisher", None),
            research_fields=research_fields,
            research_fields_id=research_fields_id,
            article_id=data.get("article_id", None),
            reborn_doi=data.get("reborn_doi", None) or data.get("rebornDOI", None),
            paper_type=data.get("paper_type", None),
            concepts=concepts,
            created_at=created_at,
            updated_at=updated_at,
        )
