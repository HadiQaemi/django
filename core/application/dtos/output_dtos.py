"""
Output Data Transfer Objects for the REBORN API.

These DTOs are used to transfer data from the application services to the API layer.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class AuthorOutputDTO(BaseModel):
    """Output DTO for an author."""

    id: str
    given_name: str
    family_name: str
    label: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ConceptOutputDTO(BaseModel):
    """Output DTO for a research concept."""

    id: str
    label: str
    identifier: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ResearchFieldOutputDTO(BaseModel):
    """Output DTO for a research field."""

    id: str
    label: str

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class JournalOutputDTO(BaseModel):
    """Output DTO for a journal."""

    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


class ConferenceOutputDTO(BaseModel):
    """Output DTO for a conference."""

    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


class NotationOutputDTO(BaseModel):
    """Output DTO for a notation."""

    id: str
    label: str
    concept: Optional[ConceptOutputDTO] = None


class StatementOutputDTO(BaseModel):
    """Output DTO for a statement."""

    id: str
    statement_id: str
    content: Dict[str, Any]
    author: List[AuthorOutputDTO]
    article_id: str
    supports: List[Dict[str, Any]] = Field(default_factory=list)
    notation: Optional[NotationOutputDTO] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ContributionOutputDTO(BaseModel):
    """Output DTO for a contribution."""

    id: str
    title: str
    author: List[AuthorOutputDTO]
    info: Dict[str, Any]
    paper_id: Optional[str] = None
    json_id: Optional[str] = None
    json_type: Optional[str] = None
    json_context: Optional[Dict[str, Any]] = None
    predicates: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class PaperOutputDTO(BaseModel):
    """Output DTO for a research paper."""

    id: str
    article_id: Optional[str] = None
    title: str
    author: List[AuthorOutputDTO]
    abstract: str
    contributions: List[ContributionOutputDTO] = Field(default_factory=list)
    statements: List[StatementOutputDTO] = Field(default_factory=list)
    dois: Optional[str] = None
    date_published: Optional[datetime] = None
    entity: Optional[str] = None
    external: Optional[str] = None
    info: Dict[str, Any] = Field(default_factory=dict)
    timeline: Dict[str, Any] = Field(default_factory=dict)
    journal: Optional[JournalOutputDTO] = None
    conference: Optional[ConferenceOutputDTO] = None
    publisher: Optional[Dict[str, Any]] = None
    research_fields: List[ResearchFieldOutputDTO] = Field(default_factory=list)
    reborn_doi: Optional[str] = None
    paper_type: Optional[str] = None
    concepts: List[ConceptOutputDTO] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchResultItemDTO(BaseModel):
    """Output DTO for a search result item."""

    id: str
    name: str
    author: str
    date: Optional[Union[str, datetime]] = None
    journal: Optional[str] = None
    article: Optional[str] = None
    publisher: Optional[str] = None
    score: Optional[float] = None


class SearchResultsDTO(BaseModel):
    """Output DTO for search results."""

    items: List[SearchResultItemDTO] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class PaginatedResponseDTO(BaseModel):
    """Output DTO for paginated responses."""

    content: List[Any] = Field(default_factory=list)
    total_elements: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class CommonResponseDTO(BaseModel):
    """Output DTO for common responses."""

    success: bool
    message: Optional[str] = None
    result: Any = None
    total_count: Optional[int] = None
