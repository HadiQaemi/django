import logging
import os
import json
import weaviate
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sentence_transformers import SentenceTransformer
from django.conf import settings

logger = logging.getLogger(__name__)


class WeaviateSearchEngine:

    def __init__(
        self,
        host: str = None,
        model_name: str = "all-MiniLM-L6-v2",
        articles_class_name: str = "Article",
        statements_class_name: str = "Statement",
        use_batch: bool = True,
        batch_size: int = 100,
    ):
        self.host = host or os.environ.get("WEAVIATE_URL", "http://localhost:8080")
        self.articles_class_name = articles_class_name
        self.statements_class_name = statements_class_name
        self.use_batch = use_batch
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device="cpu")

        try:
            self.client = weaviate.Client(self.host)
            if not self.client.is_ready():
                logger.warning(
                    "Could not connect to Weaviate. Semantic search will be disabled."
                )
                self.client = None
            else:
                logger.info("Connected to Weaviate successfully.")
                self._ensure_schema()
        except Exception as e:
            logger.warning(
                f"Could not connect to Weaviate: {str(e)}. Semantic search will be disabled."
            )
            self.client = None

    def _ensure_schema(self) -> None:
        try:
            # Define the schema for articles
            article_class_obj = {
                "class": self.articles_class_name,
                "description": "A scholarly article",
                "vectorizer": "none",  # we'll provide our own vectors
                "properties": [
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "The title of the article",
                    },
                    {
                        "name": "abstract",
                        "dataType": ["text"],
                        "description": "The abstract of the article",
                    },
                    {
                        "name": "article_id",
                        "dataType": ["string"],
                        "description": "The unique identifier of the article",
                    },
                    {
                        "name": "content_vector",
                        "dataType": ["vector"],
                        "description": "The vector representation of the article content",
                    },
                ],
            }

            # Define the schema for statements
            statement_class_obj = {
                "class": self.statements_class_name,
                "description": "A statement from a scholarly article",
                "vectorizer": "none",  # we'll provide our own vectors
                "properties": [
                    {
                        "name": "text",
                        "dataType": ["text"],
                        "description": "The text of the statement",
                    },
                    {
                        "name": "abstract",
                        "dataType": ["text"],
                        "description": "The abstract of the article containing the statement",
                    },
                    {
                        "name": "statement_id",
                        "dataType": ["string"],
                        "description": "The unique identifier of the statement",
                    },
                    {
                        "name": "content_vector",
                        "dataType": ["vector"],
                        "description": "The vector representation of the statement content",
                    },
                ],
            }

            # Check if the schema already exists
            schema = self.client.schema.get()
            existing_classes = (
                [c["class"] for c in schema["classes"]] if schema.get("classes") else []
            )

            # Create article class if it doesn't exist
            if self.articles_class_name not in existing_classes:
                self.client.schema.create_class(article_class_obj)
                logger.info(f"Created schema for {self.articles_class_name}")

            # Create statement class if it doesn't exist
            if self.statements_class_name not in existing_classes:
                self.client.schema.create_class(statement_class_obj)
                logger.info(f"Created schema for {self.statements_class_name}")

        except Exception as e:
            logger.error(f"Error ensuring schema: {str(e)}")
            raise

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode texts using the sentence transformer model."""
        return self.model.encode(texts, show_progress_bar=False, device="cpu")

    def add_articles(self, articles: List[Dict[str, str]]) -> None:
        """Add articles to the search index."""
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping add_articles.")
            return

        try:
            # Validate articles
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

            # Generate texts for embedding
            texts = [
                f"{article['title']} {article['abstract']}"
                for article in valid_articles
            ]

            # Generate embeddings
            embeddings = self._encode_texts(texts)

            if self.use_batch:
                with self.client.batch as batch:
                    batch.batch_size = self.batch_size

                    for i, article in enumerate(valid_articles):
                        properties = {
                            "title": article["title"],
                            "abstract": article["abstract"],
                            "article_id": article["article_id"],
                            "content_vector": embeddings[i].tolist(),
                        }

                        batch.add_data_object(
                            properties, self.articles_class_name, article["article_id"]
                        )
            else:
                for i, article in enumerate(valid_articles):
                    properties = {
                        "title": article["title"],
                        "abstract": article["abstract"],
                        "article_id": article["article_id"],
                        "content_vector": embeddings[i].tolist(),
                    }

                    self.client.data_object.create(
                        properties, self.articles_class_name, article["article_id"]
                    )

            logger.info(
                f"Added {len(valid_articles)} articles to Weaviate index: {self.articles_class_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_articles: {str(e)}")
            raise

    def add_statements(self, statements: List[Dict[str, str]]) -> None:
        """Add statements to the search index."""
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping add_statements.")
            return

        try:
            # Validate statements
            valid_statements = []
            for statement in statements:
                if "text" in statement and "statement_id" in statement:
                    valid_statements.append(statement)
                else:
                    logger.warning(f"Skipping invalid statement: {statement}")

            if not valid_statements:
                logger.warning("No valid statements to add")
                return

            # Generate texts for embedding
            texts = [
                f"{statement['text']} {statement.get('abstract', '')}"
                for statement in valid_statements
            ]

            # Generate embeddings
            embeddings = self._encode_texts(texts)

            if self.use_batch:
                with self.client.batch as batch:
                    batch.batch_size = self.batch_size

                    for i, statement in enumerate(valid_statements):
                        properties = {
                            "text": statement["text"],
                            "abstract": statement.get("abstract", ""),
                            "statement_id": statement["statement_id"],
                            "content_vector": embeddings[i].tolist(),
                        }

                        batch.add_data_object(
                            properties,
                            self.statements_class_name,
                            statement["statement_id"],
                        )
            else:
                for i, statement in enumerate(valid_statements):
                    properties = {
                        "text": statement["text"],
                        "abstract": statement.get("abstract", ""),
                        "statement_id": statement["statement_id"],
                        "content_vector": embeddings[i].tolist(),
                    }

                    self.client.data_object.create(
                        properties,
                        self.statements_class_name,
                        statement["statement_id"],
                    )

            logger.info(
                f"Added {len(valid_statements)} statements to Weaviate index: {self.statements_class_name}"
            )

        except Exception as e:
            logger.error(f"Error in add_statements: {str(e)}")
            raise

    def search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search articles by query."""
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_articles."
            )
            return []

        try:
            # Validate k
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            # Encode the query
            query_vector = self._encode_texts([query])[0].tolist()

            # Search Weaviate
            result = (
                self.client.query.get(
                    self.articles_class_name, ["title", "abstract", "article_id"]
                )
                .with_near_vector(
                    {
                        "vector": query_vector,
                    }
                )
                .with_limit(k)
                .do()
            )

            # Format results
            results = []
            if result and "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(self.articles_class_name, [])

                for i, obj in enumerate(objects):
                    item = {
                        "id": obj["article_id"],
                        "item": {
                            "title": obj["title"],
                            "abstract": obj["abstract"],
                            "article_id": obj["article_id"],
                        },
                        "score": 1.0 - (i / len(objects))
                        if len(objects) > 1
                        else 1.0,  # Approximate score
                    }
                    results.append(item)

            return results

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search statements by query."""
        if not self.client:
            logger.warning(
                "Weaviate client is not available. Skipping search_statements."
            )
            return []

        try:
            # Validate k
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            # Encode the query
            query_vector = self._encode_texts([query])[0].tolist()

            # Search Weaviate
            result = (
                self.client.query.get(
                    self.statements_class_name, ["text", "abstract", "statement_id"]
                )
                .with_near_vector(
                    {
                        "vector": query_vector,
                    }
                )
                .with_limit(k)
                .do()
            )

            # Format results
            results = []
            if result and "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(self.statements_class_name, [])

                for i, obj in enumerate(objects):
                    item = {
                        "id": obj["statement_id"],
                        "item": {
                            "text": obj["text"],
                            "abstract": obj["abstract"],
                            "statement_id": obj["statement_id"],
                        },
                        "score": 1.0 - (i / len(objects))
                        if len(objects) > 1
                        else 1.0,  # Approximate score
                    }
                    results.append(item)

            return results

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise

    def delete_indices(self) -> None:
        """Delete search indices."""
        if not self.client:
            logger.warning("Weaviate client is not available. Skipping delete_indices.")
            return

        try:
            # Delete classes
            self.client.schema.delete_class(self.articles_class_name)
            self.client.schema.delete_class(self.statements_class_name)

            # Recreate schema
            self._ensure_schema()

            logger.info("Weaviate indices deleted and recreated successfully.")

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            raise

    def __del__(self):
        """Clean up resources."""
        # No specific cleanup needed for Weaviate client
        pass
