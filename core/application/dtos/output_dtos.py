"""
Output Data Transfer Objects for the REBORN API.

These DTOs are used to transfer data from the application services to the API layer.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ShortAuthorOutputDTO(BaseModel):
    label: str
    orcid: Optional[str] = None
    author_id: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AuthorOutputDTO(BaseModel):
    id: str
    given_name: str
    family_name: str
    label: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ConceptOutputDTO(BaseModel):
    id: str
    label: str
    identifier: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ResearchFieldOutputDTO(BaseModel):
    id: str
    label: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ShortResearchFieldOutputDTO(BaseModel):
    label: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class JournalOutputDTO(BaseModel):
    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


class ShortJournalOutputDTO(BaseModel):
    id: str
    label: str
    publisher: Optional[str] = None


class ConferenceOutputDTO(BaseModel):
    id: str
    label: str
    publisher: Optional[Dict[str, Any]] = None


class NotationOutputDTO(BaseModel):
    id: str
    label: str
    concept: Optional[ConceptOutputDTO] = None


class StatementOutputDTO(BaseModel):
    id: str
    statement_id: str
    content: Dict[str, Any]
    authors: List[AuthorOutputDTO]
    article_id: str
    supports: List[Dict[str, Any]] = Field(default_factory=list)
    notation: Optional[NotationOutputDTO] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ShortStatementOutputDTO(BaseModel):
    id: int
    statement_id: str
    authors: List[ShortAuthorOutputDTO]
    label: str
    article_id: int
    article_name: str
    date_published: Optional[datetime] = None
    journal_conference: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ContributionOutputDTO(BaseModel):
    id: str
    title: str
    authors: List[AuthorOutputDTO]
    info: Dict[str, Any]
    paper_id: Optional[str] = None
    json_id: Optional[str] = None
    json_type: Optional[str] = None
    json_context: Optional[Dict[str, Any]] = None
    predicates: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PaperOutputDTO(BaseModel):
    id: str
    article_id: Optional[str] = None
    title: str
    authors: List[AuthorOutputDTO]
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


class ShortPaperOutputDTO(BaseModel):
    id: int
    name: str
    abstract: Optional[str] = None
    authors: List[ShortAuthorOutputDTO]
    statements: Optional[List[Any]] = None
    research_fields: Optional[List[Any]] = None
    concepts: Optional[List[Any]] = None
    date_published: Optional[datetime] = None
    journal: Optional[Dict[str, Any]] = None
    article_id: str
    dois: Optional[str] = None
    reborn_doi: Optional[str] = None
    publisher: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchResultItemDTO(BaseModel):
    id: str
    name: str
    authors: str
    date: Optional[Union[str, datetime]] = None
    journal: Optional[str] = None
    article: Optional[str] = None
    publisher: Optional[str] = None
    score: Optional[float] = None


class SearchResultsDTO(BaseModel):
    items: List[SearchResultItemDTO] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


class PaginatedResponseDTO(BaseModel):
    content: List[Any] = Field(default_factory=list)
    total_elements: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


class CommonResponseDTO(BaseModel):
    success: bool
    message: Optional[str] = None
    result: Any = None
    total_count: Optional[int] = None
