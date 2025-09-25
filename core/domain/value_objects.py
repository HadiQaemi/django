from dataclasses import dataclass
from enum import Enum


class DomainError(ValueError):
    pass


class SearchType(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class ResourceType(str, Enum):
    LOOM = "loom"
    ARTICLE = "article"
    DATASET = "dataset"
    All = "all"

class SortBy(str, Enum):
    ALPHABET = "alphabet"
    TIME = "time"


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True)
class YearRange:
    start: int
    end: int
    MIN: int = 2000
    MAX: int = 2025

    def __post_init__(self):
        if not (
            self.MIN <= self.start <= self.MAX and self.MIN <= self.end <= self.MAX
        ):
            raise DomainError("Year out of supported range.")
        if self.start > self.end:
            raise DomainError("start_year cannot be greater than end_year.")
