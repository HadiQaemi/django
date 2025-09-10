import logging
import os
import datetime
import weaviate
from weaviate.exceptions import WeaviateConnectionError
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class WeaviateSearchEngine:
    def __init__(
        self,
        host: str = None,
        grpc_port: int = 50051,
        # model_name: str = "all-MiniLM-L6-v2",
        model_name: str = "all-mpnet-base-v2",
        articles_class_name: str = "Article",
        statements_class_name: str = "Statement",
        use_batch: bool = True,
        batch_size: int = 100,
        auto_connect: bool = True,
    ):
        self.host = host or os.environ.get("WEAVIATE_URL", "http://weaviate:8080")
        self.grpc_port = int(os.environ.get("WEAVIATE_GRPC_PORT", str(grpc_port)))
        self.articles_class_name = articles_class_name
        self.statements_class_name = statements_class_name
        self.use_batch = use_batch
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device="cpu")
        self.client: Optional[weaviate.WeaviateClient] = None
        if auto_connect:
            self.initialize_client()

    def initialize_client(self) -> bool:
        try:
            if self.client is not None:
                self.client.close()
            self.client = weaviate.WeaviateClient(
                connection_params=weaviate.connect.ConnectionParams.from_url(
                    url=self.host, grpc_port=self.grpc_port
                )
            )
            self.client.connect()

            meta = self.client.get_meta()
            logger.debug(f"Weaviate metadata: {meta}")
            logger.info("Connected to Weaviate successfully")
            self._ensure_schema()
            return True

        except WeaviateConnectionError as e:
            logger.error(f"Connection to Weaviate failed: {str(e)}")
            self.client = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing Weaviate: {str(e)}")
            self.client = None
            return False

    def _ensure_schema(self) -> None:
        """Ensure required schema classes exist in Weaviate with proper configuration."""
        if self.client is None or not self.client.is_connected():
            logger.warning("Cannot ensure schema - no active Weaviate connection")
            return
        try:
            vectorizer_config = {
                "vectorizer": "text2vec-transformers",
                "vectorIndexConfig": {
                    "distance": "cosine",
                    "vectorCacheMaxObjects": 100000,
                },
                "moduleConfig": {
                    "text2vec-transformers": {
                        "poolingStrategy": "mean",
                        "vectorizeClassName": False,
                        "model": {
                            "name": "sentence-transformers/all-mpnet-base-v2",
                            "passagePrefix": "passage:",
                            "queryPrefix": "query:",
                        },
                    }
                },
            }
            article_class = {
                "class": "Article",
                "description": "A research article containing statements",
                "properties": [
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "The title of the article",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "abstract",
                        "dataType": ["text"],
                        "description": "The abstract of the article",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "article_id",
                        "dataType": ["text"],
                        "description": "The unique identifier of the article",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True  # Don't vectorize IDs
                            }
                        },
                    },
                    {
                        "name": "updated_at",
                        "dataType": ["date"],
                        "description": "When the article was last updated",
                    },
                ],
                **vectorizer_config,
            }

            statement_class = {
                "class": "Statement",
                "description": "Individual statements extracted from articles",
                "properties": [
                    {
                        "name": "label",
                        "dataType": ["text"],
                        "description": "The label of the statement",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The content of the statement",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": False,
                                "vectorizePropertyName": False,
                            }
                        },
                    },
                    {
                        "name": "statement_id",
                        "dataType": ["text"],
                        "description": "The unique identifier of the statement",
                        "moduleConfig": {
                            "text2vec-transformers": {
                                "skip": True  # Don't vectorize IDs
                            }
                        },
                    },
                    {
                        "name": "updated_at",
                        "dataType": ["date"],
                        "description": "When the statement was last updated",
                    },
                    {
                        "name": "fromArticle",
                        "dataType": ["Article"],
                        "description": "The article this statement came from",
                    },
                ],
                **vectorizer_config,
            }
            collections = self.client.collections
            if not collections.exists("Article"):
                collections.create_from_dict(article_class)
                logger.info("Created Article class schema")
            else:
                logger.debug("Article class already exists")

            if not collections.exists("Statement"):
                collections.create_from_dict(statement_class)
                logger.info("Created Statement class schema")
            else:
                logger.debug("Statement class already exists")

        except weaviate.exceptions.UnexpectedStatusCodeError as e:
            logger.error(
                f"Schema creation failed with status {e.status_code}: {e.message}"
            )
            raise RuntimeError("Failed to initialize Weaviate schema") from e
        except Exception as e:
            logger.error(f"Unexpected error ensuring schema: {str(e)}")
            raise

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=False, device="cpu")

    def add_articles(self, articles: List[Dict[str, str]]) -> None:
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping add_articles.")
            return
        try:
            valid_articles = []
            for article in articles:
                if (
                    "title" in article
                    and "abstract" in article
                    and "article_id" in article
                ):
                    valid_articles.append(article)
                else:
                    logger.warning(f"Skipping invalid article: {article}")

            if not valid_articles:
                logger.warning("No valid articles to add")
                return

            texts = [
                f"{article['title']} {article['abstract']}"
                for article in valid_articles
            ]

            embeddings = self._encode_texts(texts)
            collection = self.client.collections.get(self.articles_class_name)

            if self.use_batch:
                with collection.batch.dynamic() as batch:
                    batch.batch_size = self.batch_size

                    for i, article in enumerate(valid_articles):
                        properties = {
                            "title": article["title"],
                            "abstract": article["abstract"],
                            "article_id": article["article_id"],
                            "updated_at": article.get(
                                "updated_at", datetime.datetime.now().isoformat()
                            ),
                        }

                        batch.add_object(
                            properties=properties,
                            vector=embeddings[i].tolist(),
                            uuid=article["article_id"],
                        )
            else:
                for i, article in enumerate(valid_articles):
                    properties = {
                        "title": article["title"],
                        "abstract": article["abstract"],
                        "article_id": article["article_id"],
                        "updated_at": article.get(
                            "updated_at", datetime.datetime.now().isoformat()
                        ),
                    }

                    collection.data.insert(
                        properties=properties,
                        vector=embeddings[i].tolist(),
                        uuid=article["article_id"],
                    )

            logger.info(
                f"Added {len(valid_articles)} articles to Weaviate index: {self.articles_class_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_articles: {str(e)}")
            raise

    def add_statements(self, statements: List[Dict[str, str]]) -> None:
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping add_statements.")
            return

        try:
            valid_statements = []
            for statement in statements:
                if "label" in statement and "statement_id" in statement:
                    valid_statements.append(statement)
                else:
                    logger.warning(
                        f"Skipping invalid statement: {statement['statement_id']}"
                    )

            if not valid_statements:
                logger.warning("No valid statements to add")
                return

            texts = [
                f"{statement['label']} {statement.get('content', '')}"
                for statement in valid_statements
            ]
            embeddings = self._encode_texts(texts)
            collection = self.client.collections.get(self.statements_class_name)

            if self.use_batch:
                with collection.batch.dynamic() as batch:
                    batch.batch_size = self.batch_size
                    for i, statement in enumerate(valid_statements):
                        properties = {
                            "label": statement["label"],
                            "content": statement.get("content", ""),
                            "statement_id": statement["statement_id"],
                            "updated_at": statement.get(
                                "updated_at", datetime.datetime.now().isoformat()
                            ),
                        }

                        batch.add_object(
                            properties=properties,
                            vector=embeddings[i].tolist(),
                            uuid=statement["statement_id"],
                        )
            else:
                for i, statement in enumerate(valid_statements):
                    properties = {
                        "label": statement["label"],
                        "content": statement.get("content", ""),
                        "statement_id": statement["statement_id"],
                        "updated_at": statement.get(
                            "updated_at", datetime.datetime.now().isoformat()
                        ),
                    }

                    collection.data.insert(
                        properties=properties,
                        vector=embeddings[i].tolist(),
                        uuid=statement["statement_id"],
                    )

            logger.info(
                f"Added {len(valid_statements)} statements to Weaviate index: {self.statements_class_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_statements: {str(e)}")
            raise

    def delete_article(self, article_id: str) -> bool:
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping delete_article.")
            return False

        try:
            collection = self.client.collections.get(self.articles_class_name)

            try:
                collection.data.delete_by_id(article_id)
                logger.info(f"Deleted article from Weaviate 1: {article_id}")
                return True
            except weaviate.exceptions.WeaviateEntityNotFoundError:
                query_result = collection.query.fetch_objects(
                    filters=collection.query.filter.equal("article_id", article_id),
                    limit=1,
                )

                if query_result.objects:
                    object_uuid = query_result.objects[0].uuid
                    collection.data.delete_by_id(object_uuid)
                    logger.info(f"Deleted article from Weaviate 2: {article_id}")
                    return True
                else:
                    logger.warning(f"Article not found in Weaviate: {article_id}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting article from Weaviate: {str(e)}")
            return False

    def delete_statement(self, statement_id: str) -> bool:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping delete_statement."
            )
            return False

        try:
            collection = self.client.collections.get(self.statements_class_name)

            try:
                collection.data.delete_by_id(statement_id)
                logger.info(f"Deleted statement from Weaviate: {statement_id}")
                return True
            except weaviate.exceptions.WeaviateEntityNotFoundError:
                query_result = collection.query.fetch_objects(
                    filters=collection.query.filter.equal("statement_id", statement_id),
                    limit=1,
                )

                if query_result.objects:
                    object_uuid = query_result.objects[0].uuid
                    collection.data.delete_by_id(object_uuid)
                    logger.info(f"Deleted statement from Weaviate: {statement_id}")
                    return True
                else:
                    logger.warning(f"Statement not found in Weaviate: {statement_id}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting statement from Weaviate: {str(e)}")
            return False

    def update_article(self, article: Dict[str, str]) -> bool:
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping update_article.")
            return False

        try:
            if not all(k in article for k in ["article_id", "title", "abstract"]):
                logger.warning(f"Invalid article for update: {article}")
                return False
            self.delete_article(article["article_id"])
            self.add_articles([article])

            logger.info(f"Updated article in Weaviate: {article['article_id']}")
            return True

        except Exception as e:
            logger.error(f"Error updating article in Weaviate: {str(e)}")
            return False

    def update_statement(self, statement: Dict[str, str]) -> bool:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping update_statement."
            )
            return False

        try:
            if not all(k in statement for k in ["statement_id", "label"]):
                logger.warning(
                    f"Invalid statement for update: {statement['statement_id']}"
                )
                return False
            self.delete_statement(statement["statement_id"])
            self.add_statements([statement])

            logger.info(f"Updated statement in Weaviate: {statement['statement_id']}")
            return True

        except Exception as e:
            logger.error(f"Error updating statement in Weaviate: {str(e)}")
            return False

    def semantic_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_articles."
            )
            return []

        try:
            articles = self.client.collections.get(self.articles_class_name)
            response = articles.query.near_text(
                query=query,
                limit=5,
                return_metadata=["distance", "certainty"],
                return_properties=["title", "abstract", "article_id"],
                certainty=0.55,
            )
            results = [
                {
                    **dict(obj.properties),
                    "distance": obj.metadata.distance,
                    "certainty": obj.metadata.certainty,
                    "rank": idx + 1,
                }
                for idx, obj in enumerate(response.objects)
            ]

            return sorted(results, key=lambda x: x["certainty"], reverse=True)

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def semantic_search_statements(
        self, query: str, k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_statements."
            )
            return []
        try:
            statements = self.client.collections.get(self.statements_class_name)
            response = statements.query.near_text(
                query=query,
                limit=5,
                return_metadata=["distance", "certainty"],
                return_properties=["label", "content", "statement_id"],
                certainty=0.55,
            )
            results = [
                {
                    **dict(obj.properties),
                    "distance": obj.metadata.distance,
                    "certainty": obj.metadata.certainty,
                    "rank": idx + 1,
                }
                for idx, obj in enumerate(response.objects)
            ]

            return sorted(results, key=lambda x: x["certainty"], reverse=True)

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise

    def hybrid_search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_articles."
            )
            return []

        try:
            articles = self.client.collections.get(self.articles_class_name)
            response = articles.query.hybrid(
                query=query,
                limit=5,
                return_metadata=["distance", "score"],
                return_properties=["title", "abstract", "article_id"],
            )
            results = [
                {
                    **obj.properties,
                    "score": obj.metadata.score,
                    "distance": obj.metadata.distance,
                }
                for obj in response.objects
                if obj.metadata.score >= 0.55
            ]
            return sorted(results, key=lambda x: x["score"], reverse=True)

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def hybrid_search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_statements."
            )
            return []
        try:
            statements = self.client.collections.get(self.statements_class_name)
            response = statements.query.hybrid(
                query=query,
                limit=5,
                return_metadata=["distance", "score"],
                return_properties=["label", "content", "statement_id"],
            )
            results = [
                {
                    **obj.properties,
                    "score": obj.metadata.score,
                    "distance": obj.metadata.distance,
                }
                for obj in response.objects
                if obj.metadata.score >= 0.55
            ]
            return sorted(results, key=lambda x: x["score"], reverse=True)

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise

    def delete_indices(self) -> None:
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping delete_indices.")
            return

        try:
            try:
                self.client.collections.delete(self.articles_class_name)
            except weaviate.exceptions.WeaviateEntityNotFoundError:
                logger.info(f"Collection {self.articles_class_name} does not exist")

            try:
                self.client.collections.delete(self.statements_class_name)
            except weaviate.exceptions.WeaviateEntityNotFoundError:
                logger.info(f"Collection {self.statements_class_name} does not exist")
            self._ensure_schema()

            logger.info("Weaviate indices deleted and recreated successfully.")

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            raise

    def __del__(self):
        pass
