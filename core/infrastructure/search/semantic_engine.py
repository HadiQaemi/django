"""
Semantic search engine implementation.

This module implements a semantic search engine using sentence transformers and FAISS.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional, Any
import faiss
import json
import gc
import os
import logging
import torch

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Semantic search engine implementation."""

    def __init__(
        self,
        # model_name: str = "all-MiniLM-L6-v2",
        model_name: str = "all-mpnet-base-v2",
        batch_size: int = 32,
        use_gpu: bool = False,
        articles_index_name: str = "articles_index",
        statements_index_name: str = "statements_index",
        base_path: str = "data",
    ):
        """Initialize the search engine."""
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        self.model = SentenceTransformer(model_name, device="cpu")
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        self.articles_index_name = articles_index_name
        self.statements_index_name = statements_index_name
        self.base_path = base_path

        self.articles_index = None
        self.statements_index = None
        self.articles = []
        self.statements = []

        if self.use_gpu and torch.cuda.is_available():
            self.res = faiss.StandardGpuResources()

        self._load_indices()

    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """Encode texts using the sentence transformer model."""
        embeddings_list = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            batch_embeddings = self.model.encode(
                batch_texts, show_progress_bar=True, device="cpu"
            )
            embeddings_list.append(batch_embeddings)
        return np.vstack(embeddings_list)

    def _load_indices(self) -> None:
        """Load indices from disk."""
        try:
            # Ensure base directory exists
            os.makedirs(self.base_path, exist_ok=True)

            articles_index_path = f"{self.base_path}/{self.articles_index_name}.index"
            articles_data_path = f"{self.base_path}/{self.articles_index_name}.json"

            if os.path.exists(articles_index_path) and os.path.exists(
                articles_data_path
            ):
                self.articles_index = faiss.read_index(articles_index_path)
                with open(articles_data_path, "r") as f:
                    self.articles = json.load(f)
                logger.info(
                    f"Articles index and data loaded from {articles_index_path}"
                )

            statements_index_path = (
                f"{self.base_path}/{self.statements_index_name}.index"
            )
            statements_data_path = f"{self.base_path}/{self.statements_index_name}.json"

            if os.path.exists(statements_index_path) and os.path.exists(
                statements_data_path
            ):
                self.statements_index = faiss.read_index(statements_index_path)
                with open(statements_data_path, "r") as f:
                    self.statements = json.load(f)
                logger.info(
                    f"Statements index and data loaded from {statements_index_path}"
                )

        except Exception as e:
            logger.error(f"Failed to load indices: {str(e)}")

    def _save_indices(self) -> None:
        """Save indices to disk."""
        try:
            # Ensure base directory exists
            os.makedirs(self.base_path, exist_ok=True)

            if self.articles_index is not None:
                articles_index_path = (
                    f"{self.base_path}/{self.articles_index_name}.index"
                )
                articles_data_path = f"{self.base_path}/{self.articles_index_name}.json"

                faiss.write_index(self.articles_index, articles_index_path)
                with open(articles_data_path, "w") as f:
                    json.dump(self.articles, f)

                logger.info(f"Articles index and data saved to {articles_index_path}")

            if self.statements_index is not None:
                statements_index_path = (
                    f"{self.base_path}/{self.statements_index_name}.index"
                )
                statements_data_path = (
                    f"{self.base_path}/{self.statements_index_name}.json"
                )

                faiss.write_index(self.statements_index, statements_index_path)
                with open(statements_data_path, "w") as f:
                    json.dump(self.statements, f)

                logger.info(
                    f"Statements index and data saved to {statements_index_path}"
                )

        except Exception as e:
            logger.error(f"Failed to save indices: {str(e)}")

    def add_articles(self, articles: List[Dict[str, str]]) -> None:
        """Add articles to the search index."""
        try:
            self._load_indices()

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

            # Add articles to the list
            self.articles.extend(valid_articles)

            # Generate texts for embedding
            texts = [
                f"{article['title']} {article['abstract']}"
                for article in valid_articles
            ]

            # Generate embeddings
            embeddings = self._encode_texts(texts)
            dimension = embeddings.shape[1]

            # Initialize index if needed
            if self.articles_index is None:
                self.articles_index = faiss.IndexFlatL2(dimension)
                if self.use_gpu and torch.cuda.is_available():
                    self.articles_index = faiss.index_cpu_to_gpu(
                        self.res, 0, self.articles_index
                    )

            # Add embeddings to index
            self.articles_index.add(np.ascontiguousarray(embeddings.astype("float32")))

            # Clean up
            del embeddings
            gc.collect()

            # Save indices
            self._save_indices()

            logger.info(f"Added {len(valid_articles)} articles to the search index")

        except Exception as e:
            logger.error(f"Error in add_articles: {str(e)}")
            raise

    def add_statements(self, statements: List[Dict[str, str]]) -> None:
        """Add statements to the search index."""
        try:
            self._load_indices()

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

            # Add statements to the list
            self.statements.extend(valid_statements)

            # Generate texts for embedding
            texts = [
                f"{statement['text']} {statement.get('abstract', '')}"
                for statement in valid_statements
            ]

            # Generate embeddings
            embeddings = self._encode_texts(texts)
            dimension = embeddings.shape[1]

            # Initialize index if needed
            if self.statements_index is None:
                self.statements_index = faiss.IndexFlatL2(dimension)
                if self.use_gpu and torch.cuda.is_available():
                    self.statements_index = faiss.index_cpu_to_gpu(
                        self.res, 0, self.statements_index
                    )

            # Add embeddings to index
            self.statements_index.add(
                np.ascontiguousarray(embeddings.astype("float32"))
            )

            # Clean up
            del embeddings
            gc.collect()

            # Save indices
            self._save_indices()

            logger.info(f"Added {len(valid_statements)} statements to the search index")

        except Exception as e:
            logger.error(f"Error in add_statements: {str(e)}")
            raise

    def search_articles(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search articles by query."""
        try:
            if self.articles_index is None:
                self._load_indices()
                if self.articles_index is None:
                    logger.warning("Articles index is not initialized")
                    return []

            # Validate k
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            # Search index
            query_vector = self.model.encode([query], device="cpu")
            distances, indices = self.articles_index.search(
                np.ascontiguousarray(query_vector.astype("float32")), k
            )

            return self._format_results(
                indices[0], distances[0], self.articles, "article_id"
            )

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def search_statements(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search statements by query."""
        try:
            if self.statements_index is None:
                self._load_indices()
                if self.statements_index is None:
                    logger.warning("Statements index is not initialized")
                    return []

            # Validate k
            if k <= 0:
                logger.warning(f"Invalid k: {k}, using default value 5")
                k = 5

            # Search index
            query_vector = self.model.encode([query], device="cpu")
            distances, indices = self.statements_index.search(
                np.ascontiguousarray(query_vector.astype("float32")), k
            )

            return self._format_results(
                indices[0], distances[0], self.statements, "statement_id"
            )

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise

    def _format_results(
        self,
        indices: np.ndarray,
        distances: np.ndarray,
        data: List[Dict[str, Any]],
        id_field: str,
    ) -> List[Dict[str, Any]]:
        """Format search results."""
        results = []

        for idx, (distance, index) in enumerate(zip(distances, indices)):
            if index >= 0 and index < len(data):
                results.append(
                    {
                        "item": data[index],
                        "score": float(1 / (1 + distance)),
                        "id": data[index].get(id_field, None),
                    }
                )

        return results

    def delete_indices(self) -> None:
        """Delete search indices."""
        try:
            articles_index_path = f"{self.base_path}/{self.articles_index_name}.index"
            articles_data_path = f"{self.base_path}/{self.articles_index_name}.json"

            if os.path.exists(articles_index_path):
                os.remove(articles_index_path)
                logger.info(f"Deleted {articles_index_path}")

            if os.path.exists(articles_data_path):
                os.remove(articles_data_path)
                logger.info(f"Deleted {articles_data_path}")

            statements_index_path = (
                f"{self.base_path}/{self.statements_index_name}.index"
            )
            statements_data_path = f"{self.base_path}/{self.statements_index_name}.json"

            if os.path.exists(statements_index_path):
                os.remove(statements_index_path)
                logger.info(f"Deleted {statements_index_path}")

            if os.path.exists(statements_data_path):
                os.remove(statements_data_path)
                logger.info(f"Deleted {statements_data_path}")

            # Reset in-memory indices
            self.articles_index = None
            self.statements_index = None
            self.articles = []
            self.statements = []

            logger.info("Search indices deleted successfully")

        except Exception as e:
            logger.error(f"Error in delete_indices: {str(e)}")
            raise

    def __del__(self) -> None:
        """Clean up resources."""
        if hasattr(self, "articles_index") and self.articles_index is not None:
            del self.articles_index

        if hasattr(self, "statements_index") and self.statements_index is not None:
            del self.statements_index

        gc.collect()
