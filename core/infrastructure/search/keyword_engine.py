from elasticsearch import Elasticsearch, NotFoundError
from typing import List, Dict, Any, Optional
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


class KeywordSearchEngine:

    def __init__(
        self,
        host: str = None,
        articles_index_name: str = "articles_index",
        statements_index_name: str = "statements_index",
    ):
        self.host = host or os.environ.get("ELASTIC_URL", "http://localhost:9200")
        self.articles_index_name = articles_index_name
        self.statements_index_name = statements_index_name

        try:
            self.client = Elasticsearch(self.host)

            if not self.client.ping():
                logger.warning(
                    "Could not connect to Elasticsearch. Keyword search will be disabled."
                )
                self.client = None
            else:
                logger.info("Connected to Elasticsearch successfully.")

        except Exception as e:
            logger.warning(
                f"Could not connect to Elasticsearch: {str(e)}. Keyword search will be disabled."
            )
            self.client = None

    def _create_index(self, index_name: str) -> None:
        if not self.client:
            return

        try:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name)
                logger.info(f"Created index: {index_name}")
            else:
                logger.info(f"Index already exists: {index_name}")

        except Exception as e:
            logger.error(f"Error creating index {index_name}: {str(e)}")
            raise

    def add_articles(self, articles: List[Dict[str, str]]) -> None:
        if not self.client:
            logger.warning(
                "Elasticsearch client is not available. Skipping add_articles."
            )
            return

        try:
            self._create_index(self.articles_index_name)

            valid_articles = []
            for article in articles:
                if "title" in article and "article_id" in article:
                    valid_articles.append(article)
                else:
                    logger.warning(f"Skipping invalid article: {article}")

            if not valid_articles:
                logger.warning("No valid articles to add")
                return

            for article in valid_articles:
                self.client.index(
                    index=self.articles_index_name,
                    id=article.get("article_id"),
                    document={
                        "title": article.get("title", ""),
                        "abstract": article.get("abstract", ""),
                        "article_id": article.get("article_id", ""),
                    },
                )

            self.client.indices.refresh(index=self.articles_index_name)

            logger.info(
                f"Added {len(valid_articles)} articles to index: {self.articles_index_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_articles: {str(e)}")
            raise

    def add_statements(self, statements: List[Dict[str, str]]) -> None:
        if not self.client:
            logger.warning(
                "Elasticsearch client is not available. Skipping add_statements."
            )
            return

        try:
            self._create_index(self.statements_index_name)

            valid_statements = []
            for statement in statements:
                if "text" in statement and "statement_id" in statement:
                    valid_statements.append(statement)
                else:
                    logger.warning(f"Skipping invalid statement: {statement}")

            if not valid_statements:
                logger.warning("No valid statements to add")
                return

            for statement in valid_statements:
                self.client.index(
                    index=self.statements_index_name,
                    id=statement.get("statement_id"),
                    document={
                        "text": statement.get("text", ""),
                        "abstract": statement.get("abstract", ""),
                        "statement_id": statement.get("statement_id", ""),
                    },
                )

            self.client.indices.refresh(index=self.statements_index_name)

            logger.info(
                f"Added {len(valid_statements)} statements to index: {self.statements_index_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_statements: {str(e)}")
            raise

    def search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Elasticsearch client is not available. Skipping search_articles."
            )
            return []

        try:
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            if not self.client.indices.exists(index=self.articles_index_name):
                logger.warning(f"Index not found: {self.articles_index_name}")
                return []

            response = self.client.search(
                index=self.articles_index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "abstract"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    "size": k,
                },
            )

            return self._format_results(response, "article_id")

        except NotFoundError:
            logger.error(f"Index not found: {self.articles_index_name}")
            return []

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Elasticsearch client is not available. Skipping search_statements."
            )
            return []

        try:
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            if not self.client.indices.exists(index=self.statements_index_name):
                logger.warning(f"Index not found: {self.statements_index_name}")
                return []

            response = self.client.search(
                index=self.statements_index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["text", "abstract"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    "size": k,
                },
            )

            return self._format_results(response, "statement_id")

        except NotFoundError:
            logger.error(f"Index not found: {self.statements_index_name}")
            return []

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise

    def _format_results(
        self, response: Dict[str, Any], id_field: str
    ) -> List[Dict[str, Any]]:
        results = []

        for hit in response["hits"]["hits"]:
            results.append(
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "data": hit["_source"],
                    id_field: hit["_source"].get(id_field),
                }
            )

        return results

    def delete_indices(self) -> None:
        if not self.client:
            logger.warning(
                "Elasticsearch client is not available. Skipping delete_indices."
            )
            return

        try:
            for index_name in [self.articles_index_name, self.statements_index_name]:
                if self.client.indices.exists(index=index_name):
                    self.client.indices.delete(index=index_name)
                    logger.info(f"Deleted index: {index_name}")
                else:
                    logger.info(f"Index does not exist: {index_name}")

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            raise

    def __del__(self) -> None:
        if hasattr(self, "client") and self.client:
            self.client.close()
            logger.info("Elasticsearch client closed.")
