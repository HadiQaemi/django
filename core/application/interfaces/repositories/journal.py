from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from core.domain.entities import Journal


class JournalRepository(ABC):
    @abstractmethod
    def get_academic_publishers_by_name(self, name: str) -> List[Journal]:
        pass

    @abstractmethod
    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        pass
