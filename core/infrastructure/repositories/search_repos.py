import logging
from typing import List, Dict, Any, Tuple
import os

from core.application.interfaces.repositories import SearchRepository
from core.infrastructure.search.semantic_engine import SemanticSearchEngine
from core.infrastructure.search.keyword_engine import KeywordSearchEngine
from core.infrastructure.search.hybrid_engine import HybridSearchEngine
from core.infrastructure.search.weaviate_engine import WeaviateSearchEngine
from core.domain.exceptions import SearchEngineError

logger = logging.getLogger(__name__)


class SearchRepositoryImpl(SearchRepository):
    def __init__(self):
        self.use_weaviate = os.environ.get("USE_WEAVIATE", "false").lower() == "true"

        try:
            if self.use_weaviate:
                logger.info("Using Weaviate for semantic search")
                self.semantic_engine = WeaviateSearchEngine()
                self.keyword_engine = KeywordSearchEngine()
                self.hybrid_engine = WeaviateSearchEngine()
            else:
                logger.info("Using default semantic search engines")
                self.semantic_engine = SemanticSearchEngine()
                self.keyword_engine = KeywordSearchEngine()
                self.hybrid_engine = HybridSearchEngine(
                    self.semantic_engine, self.keyword_engine
                )
        except Exception as e:
            logger.error(f"Error initializing search engines: {str(e)}")
            if self.use_weaviate:
                self.semantic_engine = WeaviateSearchEngine()
                self.hybrid_engine = WeaviateSearchEngine()
            else:
                self.semantic_engine = SemanticSearchEngine()
                self.keyword_engine = None
                self.hybrid_engine = HybridSearchEngine(
                    self.semantic_engine, keyword_engine=False
                )

    def semantic_search_statements(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        try:
            results = self.semantic_engine.semantic_search_statements(query, k)
            return results
        except Exception as e:
            logger.error(f"Error in semantic_search_statements: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform semantic search on statements: {str(e)}"
            )

    def semantic_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.semantic_engine.semantic_search_articles(query, k)
            return results
        except Exception as e:
            logger.error(f"Error in semantic_search_articles: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform semantic search on articles: {str(e)}"
            )

    def keyword_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            if self.keyword_engine:
                results = self.keyword_engine.search_statements(query, k)
                return results
            return []
        except Exception as e:
            logger.error(f"Error in keyword_search_statements: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform keyword search on statements: {str(e)}"
            )

    def keyword_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            if self.keyword_engine:
                results = self.keyword_engine.search_articles(query, k)
                return results
            return []
        except Exception as e:
            logger.error(f"Error in keyword_search_articles: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform keyword search on articles: {str(e)}"
            )

    def hybrid_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.hybrid_engine.hybrid_search_statements(query, k)
            return results
        except Exception as e:
            logger.error(f"Error in hybrid_search_statements: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform hybrid search on statements: {str(e)}"
            )

    def hybrid_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.hybrid_engine.hybrid_search_articles(query, k)
            return results
        except Exception as e:
            logger.error(f"Error in hybrid_search_articles: {str(e)}")
            raise SearchEngineError(
                f"Failed to perform hybrid search on articles: {str(e)}"
            )

    def add_statements(self, statements: List[Dict[str, str]]) -> bool:
        try:
            self.semantic_engine.add_statements(statements)
            if self.keyword_engine:
                self.keyword_engine.add_statements(statements)
            return True
        except Exception as e:
            logger.error(f"Error in add_statements: {str(e)}")
            raise SearchEngineError(
                f"Failed to add statements to search index: {str(e)}"
            )

    def add_articles(self, articles: List[Dict[str, str]]) -> bool:
        try:
            self.semantic_engine.add_articles(articles)
            if self.keyword_engine:
                self.keyword_engine.add_articles(articles)
            return True
        except Exception as e:
            logger.error(f"Error in add_articles: {str(e)}")
            raise SearchEngineError(f"Failed to add articles to search index: {str(e)}")

    def delete_indices(self) -> bool:
        try:
            self.semantic_engine.delete_indices()
            if self.keyword_engine:
                self.keyword_engine.delete_indices()
            return True
        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            raise SearchEngineError(f"Failed to delete search indices: {str(e)}")

    def delete_article(self, article_id: str) -> bool:
        try:
            if self.use_weaviate and isinstance(
                self.semantic_engine, WeaviateSearchEngine
            ):
                result = self.semantic_engine.delete_article(article_id)
                if not result:
                    logger.warning(
                        f"Failed to delete article from Weaviate: {article_id}"
                    )

            if self.keyword_engine:
                try:
                    self.keyword_engine.delete_article(article_id)
                except (AttributeError, NotImplementedError) as e:
                    logger.warning(
                        f"Keyword engine does not support delete_article: {str(e)}"
                    )

            return True
        except Exception as e:
            logger.error(f"Error in delete_article: {str(e)}")
            raise SearchEngineError(
                f"Failed to delete article from search indices: {str(e)}"
            )

    def delete_statement(self, statement_id: str) -> bool:
        try:
            if self.use_weaviate and isinstance(
                self.semantic_engine, WeaviateSearchEngine
            ):
                result = self.semantic_engine.delete_statement(statement_id)
                if not result:
                    logger.warning(
                        f"Failed to delete statement from Weaviate: {statement_id}"
                    )

            if self.keyword_engine:
                try:
                    self.keyword_engine.delete_statement(statement_id)
                except (AttributeError, NotImplementedError) as e:
                    logger.warning(
                        f"Keyword engine does not support delete_statement: {str(e)}"
                    )

            return True
        except Exception as e:
            logger.error(f"Error in delete_statement: {str(e)}")
            raise SearchEngineError(
                f"Failed to delete statement from search indices: {str(e)}"
            )

    def update_article(self, article: Dict[str, str]) -> bool:
        try:
            if self.use_weaviate and isinstance(
                self.semantic_engine, WeaviateSearchEngine
            ):
                result = self.semantic_engine.update_article(article)
                if not result:
                    logger.warning(
                        f"Failed to update article in Weaviate: {article.get('article_id')}"
                    )

            else:
                self.add_articles([article])

            return True
        except Exception as e:
            logger.error(f"Error in update_article: {str(e)}")
            raise SearchEngineError(
                f"Failed to update article in search indices: {str(e)}"
            )

    def update_statement(self, statement: Dict[str, str]) -> bool:
        try:
            if self.use_weaviate and isinstance(
                self.semantic_engine, WeaviateSearchEngine
            ):
                result = self.semantic_engine.update_statement(statement)
                if not result:
                    logger.warning(
                        f"Failed to update statement in Weaviate: {statement.get('statement_id')}"
                    )

            else:
                self.add_statements([statement])

            return True
        except Exception as e:
            logger.error(f"Error in update_statement: {str(e)}")
            raise SearchEngineError(
                f"Failed to update statement in search indices: {str(e)}"
            )
