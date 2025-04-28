"""
Domain entities for the REBORN API.

These are pure domain entities independent of any infrastructure concerns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class Author:
    """Author of a research paper or contribution."""

    id: str
    given_name: str
    family_name: str
    label: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the author's full name."""
        return f"{self.given_name} {self.family_name}"


@dataclass
class Journal:
    """Academic journal where a paper was published."""

    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


@dataclass
class Conference:
    """Academic conference where a paper was presented."""

    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


@dataclass
class Concept:
    """Research concept or keyword."""

    id: str
    label: str
    identifier: Optional[str] = None


@dataclass
class ResearchField:
    """Field of research for a paper."""

    id: str
    label: str


@dataclass
class Notation:
    """Notation for a statement."""

    id: str
    label: str
    concept: Optional[Concept] = None


@dataclass
class Statement:
    """Statement or claim made in a paper."""

    id: str
    content: Dict[str, Any]
    author: List[Author]
    article_id: str
    supports: List[Dict[str, Any]] = field(default_factory=list)
    notation: Optional[Notation] = None
    statement_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Contribution:
    """Contribution to a research paper."""

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
class Paper:
    """Research paper with its metadata and contributions."""

    id: str
    title: str
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
    publisher: Optional[Dict[str, Any]] = None
    research_fields: List[ResearchField] = field(default_factory=list)
    research_fields_id: List[str] = field(default_factory=list)
    article_id: Optional[str] = None
    reborn_doi: Optional[str] = None
    paper_type: Optional[str] = None
    concepts: List[Concept] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
