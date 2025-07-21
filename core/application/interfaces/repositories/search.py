from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SearchRepository(ABC):
    @abstractmethod
    def semantic_search_statements(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def semantic_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def keyword_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def keyword_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def hybrid_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def hybrid_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_statements(self, statements: List[Dict[str, str]]) -> bool:
        pass

    @abstractmethod
    def add_articles(self, articles: List[Dict[str, str]]) -> bool:
        pass

    @abstractmethod
    def delete_indices(self) -> bool:
        pass

    @abstractmethod
    def delete_article(self, article_id: str) -> bool:
        pass

    @abstractmethod
    def delete_statement(self, statement_id: str) -> bool:
        pass

    @abstractmethod
    def update_article(self, article: Dict[str, str]) -> bool:
        pass

    @abstractmethod
    def update_statement(self, statement: Dict[str, str]) -> bool:
        pass
