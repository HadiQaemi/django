from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

from core.application.dtos.output_dtos import ShortScholarityOutputDTO


@dataclass
class Author:
    id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    orcid: Optional[str] = None
    author_id: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None
    affiliation: Optional[Any] = None

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}"

    def formatted_orcid(self):
        if self.orcid and self.orcid.startswith("https://orcid.org"):
            return self


@dataclass
class Journal:
    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None
    journal_conference_id: Optional[str] = None
    _id: Optional[str] = None


@dataclass
class Conference:
    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


@dataclass
class Concept:
    id: str
    label: str
    concept_id: Optional[str] = None
    identifier: Optional[str] = None


@dataclass
class ResearchField:
    id: str
    label: str
    related_identifier: Optional[str] = None
    research_field_id: Optional[str] = None


@dataclass
class Notation:
    id: str
    label: str
    concept: Optional[Concept] = None


@dataclass
class Statement:
    id: str
    label: str
    # content: Dict[str, Any]
    author: List[Author]
    article_id: str
    article_name: str
    date_published: str
    journal_conference: str
    supports: List[Dict[str, Any]] = field(default_factory=list)
    article: Optional[List[Dict[str, Any]]] = None
    # notation: Optional[Notation] = None
    statement_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Contribution:
    id: str
    title: str
    author: List[Author]
    info: Dict[str, Any]
    paper_id: Optional[str] = None
    json_id: Optional[str] = None
    json_type: Optional[str] = None
    json_context: Optional[Dict[str, Any]] = None
    predicates: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Article:
    id: str
    name: str
    authors: List[Author]
    abstract: str
    contributions: List[Contribution] = field(default_factory=list)
    statements: List[Statement] = field(default_factory=list)
    dois: Optional[str] = None
    date_published: Optional[datetime] = None
    entity: Optional[str] = None
    external: Optional[str] = None
    info: Optional[Dict[str, Any]] = field(default_factory=dict)
    timeline: Optional[Dict[str, Any]] = field(default_factory=dict)
    journal: Optional[Journal] = None
    conference: Optional[Conference] = None
    publisher: str = None
    research_fields: List[ResearchField] = field(default_factory=list)
    research_fields_id: List[str] = field(default_factory=list)
    related_items: Optional[List[ShortScholarityOutputDTO]] = None
    article_id: Optional[str] = None
    reborn_doi: Optional[str] = None
    paper_type: Optional[Any] = None
    concepts: List[Concept] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
