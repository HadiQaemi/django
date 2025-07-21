
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CacheRepository(ABC):
    @abstractmethod
    def get_schema_by_type_id(self, type_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    def save_schema(self, type_id: str, schema_data: Dict[str, Any]) -> Any:
        pass
