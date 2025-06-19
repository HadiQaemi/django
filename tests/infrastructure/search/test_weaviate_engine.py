import pytest
import unittest
from unittest.mock import patch, MagicMock, ANY

from core.infrastructure.search.weaviate_engine import WeaviateSearchEngine


class TestWeaviateSearchEngine(unittest.TestCase):
    @patch("core.infrastructure.search.weaviate_engine.weaviate")
    @patch("core.infrastructure.search.weaviate_engine.SentenceTransformer")
    def setUp(self, mock_transformer, mock_weaviate):
        self.mock_client = MagicMock()
        self.mock_client.is_ready.return_value = True
        mock_weaviate.Client.return_value = self.mock_client

        self.mock_model = MagicMock()
        mock_transformer.return_value = self.mock_model

        self.engine = WeaviateSearchEngine(
            host="http://weaviate:8080",
            # model_name="all-MiniLM-L6-v2",
            model_name="sentence-transformers-all-mpnet-base-v2",
            articles_class_name="TestArticle",
            statements_class_name="TestStatement",
        )

    def test_initialization(self):
        assert self.engine.client is not None
        assert self.engine.articles_class_name == "TestArticle"
        assert self.engine.statements_class_name == "TestStatement"
        assert self.mock_client.schema.create_class.call_count == 2

    @patch("core.infrastructure.search.weaviate_engine.weaviate")
    @patch("core.infrastructure.search.weaviate_engine.SentenceTransformer")
    def test_initialization_failure(self, mock_transformer, mock_weaviate):
        mock_client = MagicMock()
        mock_client.is_ready.return_value = False
        mock_weaviate.Client.return_value = mock_client
        engine = WeaviateSearchEngine()
        assert engine.client is None

    def test_encode_texts(self):
        self.mock_model.encode.return_value = [0.1, 0.2, 0.3]
        result = self.engine._encode_texts(["test text"])
        self.mock_model.encode.assert_called_once_with(
            ["test text"], show_progress_bar=False, device="cpu"
        )
        assert result == [0.1, 0.2, 0.3]

    def test_add_articles(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        batch_mock = MagicMock()
        self.mock_client.batch.__enter__.return_value = batch_mock
        articles = [
            {
                "article_id": "123",
                "title": "Test Article",
                "abstract": "This is a test abstract",
            }
        ]
        self.engine.add_articles(articles)
        batch_mock.add_data_object.assert_called_once_with(
            {
                "title": "Test Article",
                "abstract": "This is a test abstract",
                "article_id": "123",
                "content_vector": [0.1, 0.2, 0.3],
            },
            "TestArticle",
            "123",
        )

    def test_add_statements(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        batch_mock = MagicMock()
        self.mock_client.batch.__enter__.return_value = batch_mock
        statements = [
            {
                "statement_id": "456",
                "text": "Test Statement",
                "abstract": "This is a test abstract",
            }
        ]
        self.engine.add_statements(statements)
        batch_mock.add_data_object.assert_called_once_with(
            {
                "text": "Test Statement",
                "abstract": "This is a test abstract",
                "statement_id": "456",
                "content_vector": [0.1, 0.2, 0.3],
            },
            "TestStatement",
            "456",
        )

    def test_search_articles(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        query_builder.do.return_value = {
            "data": {
                "Get": {
                    "TestArticle": [
                        {
                            "title": "Test Article",
                            "abstract": "This is a test abstract",
                            "article_id": "123",
                        }
                    ]
                }
            }
        }
        results = self.engine.search_articles("test query", 5)
        self.mock_client.query.get.assert_called_once_with(
            "TestArticle", ["title", "abstract", "article_id"]
        )
        query_builder.with_near_vector.assert_called_once_with(
            {
                "vector": [0.1, 0.2, 0.3],
            }
        )
        query_builder.with_limit.assert_called_once_with(5)
        assert len(results) == 1
        assert results[0]["id"] == "123"
        assert results[0]["item"]["title"] == "Test Article"
        assert results[0]["item"]["abstract"] == "This is a test abstract"
        assert results[0]["score"] == 1.0

    def test_search_statements(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder
        query_builder.do.return_value = {
            "data": {
                "Get": {
                    "TestStatement": [
                        {
                            "text": "Test Statement",
                            "abstract": "This is a test abstract",
                            "statement_id": "456",
                        }
                    ]
                }
            }
        }
        results = self.engine.search_statements("test query", 5)

        self.mock_client.query.get.assert_called_once_with(
            "TestStatement", ["text", "abstract", "statement_id"]
        )
        query_builder.with_near_vector.assert_called_once_with(
            {
                "vector": [0.1, 0.2, 0.3],
            }
        )
        query_builder.with_limit.assert_called_once_with(5)

        assert len(results) == 1
        assert results[0]["id"] == "456"
        assert results[0]["item"]["text"] == "Test Statement"
        assert results[0]["item"]["abstract"] == "This is a test abstract"
        assert results[0]["score"] == 1.0

    def test_search_articles_empty_result(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        query_builder.do.return_value = {"data": {"Get": {}}}

        results = self.engine.search_articles("test query", 5)

        assert len(results) == 0

    def test_search_articles_with_invalid_k(self):
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        query_builder.do.return_value = {
            "data": {
                "Get": {
                    "TestArticle": [
                        {
                            "title": "Test Article",
                            "abstract": "This is a test abstract",
                            "article_id": "123",
                        }
                    ]
                }
            }
        }

        results = self.engine.search_articles("test query", -1)
        query_builder.with_limit.assert_called_once_with(5)

    def test_delete_indices(self):
        self.engine.delete_indices()

        self.mock_client.schema.delete_class.assert_any_call("TestArticle")
        self.mock_client.schema.delete_class.assert_any_call("TestStatement")

        assert self.mock_client.schema.create_class.call_count >= 2

    def test_client_not_available(self):
        self.engine.client = None

        self.engine.add_articles(
            [{"article_id": "123", "title": "Test", "abstract": "Test"}]
        )
        self.engine.add_statements(
            [{"statement_id": "456", "text": "Test", "abstract": "Test"}]
        )
        results = self.engine.search_articles("test", 5)
        results_statements = self.engine.search_statements("test", 5)
        self.engine.delete_indices()

        assert results == []
        assert results_statements == []
