"""
Input Data Transfer Objects for the REBORN API.

These DTOs are used to validate and transfer data from the API layer to the application services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


class AuthorInputDTO(BaseModel):
    """Input DTO for an author."""

    id: Optional[str] = None
    given_name: str
    family_name: str
    label: Optional[str] = None


class ConceptInputDTO(BaseModel):
    """Input DTO for a research concept."""

    id: Optional[str] = None
    label: str
    identifier: Optional[str] = None


class ResearchFieldInputDTO(BaseModel):
    """Input DTO for a research field."""

    id: Optional[str] = None
    label: str


class NotationInputDTO(BaseModel):
    """Input DTO for a notation."""

    id: Optional[str] = None
    label: str
    concept: Optional[ConceptInputDTO] = None


class StatementInputDTO(BaseModel):
    """Input DTO for a statement."""

    content: Dict[str, Any]
    authors: List[AuthorInputDTO]
    article_id: str
    supports: List[Dict[str, Any]] = []
    notation: Optional[NotationInputDTO] = None
    id: Optional[str] = None
    statement_id: Optional[str] = None


class ContributionInputDTO(BaseModel):
    """Input DTO for a contribution."""

    title: str
    authors: List[AuthorInputDTO]
    info: Dict[str, Any]
    paper_id: Optional[str] = None
    json_id: Optional[str] = None
    json_type: Optional[str] = None
    json_context: Optional[Dict[str, Any]] = None
    predicates: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class PaperInputDTO(BaseModel):
    """Input DTO for a research paper."""

    title: str
    authors: List[AuthorInputDTO]
    # abstract: str
    dois: Optional[str] = None
    date_published: Optional[datetime] = None
    entity: Optional[str] = None
    external: Optional[HttpUrl] = None
    info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    journal: Optional[Dict[str, Any]] = None
    conference: Optional[Dict[str, Any]] = None
    publisher: Optional[Dict[str, Any]] = None
    research_fields: Optional[List[ResearchFieldInputDTO]] = Field(default_factory=list)
    paper_type: Optional[str] = None
    id: Optional[str] = None
    article_id: Optional[str] = None

    @validator("research_fields", pre=True, always=True)
    def set_research_fields(cls, v):
        """Default to empty list if research_fields is None."""
        return v or []


class QueryFilterInputDTO(BaseModel):
    """Input DTO for query filtering."""

    title: Optional[str] = None
    start_year: Optional[int] = 2000
    end_year: Optional[int] = datetime.now().year
    author_ids: Optional[List[str]] = Field(default_factory=list)
    journal_names: Optional[List[str]] = Field(default_factory=list)
    conference_names: Optional[List[str]] = Field(default_factory=list)
    concept_ids: Optional[List[str]] = Field(default_factory=list)
    research_fields: Optional[List[str]] = Field(default_factory=list)
    page: int = 1
    per_page: int = 10


class SearchInputDTO(BaseModel):
    """Input DTO for search queries."""

    query: str
    search_type: str = "hybrid"  # hybrid, semantic, or keyword
    sort_order: str = "a-z"  # a-z, z-a, newest
    page: int = 1
    page_size: int = 10
    research_fields: Optional[List[str]] = Field(default_factory=list)


class ScraperUrlInputDTO(BaseModel):
    """Input DTO for the scraper URL."""

    url: HttpUrl
