import pytest
import unittest
from unittest.mock import patch, MagicMock, ANY

from core.infrastructure.search.weaviate_engine import WeaviateSearchEngine


class TestWeaviateSearchEngine(unittest.TestCase):
    """Tests for the Weaviate search engine."""

    @patch("core.infrastructure.search.weaviate_engine.weaviate")
    @patch("core.infrastructure.search.weaviate_engine.SentenceTransformer")
    def setUp(self, mock_transformer, mock_weaviate):
        """Set up the test environment."""
        # Mock the Weaviate client
        self.mock_client = MagicMock()
        self.mock_client.is_ready.return_value = True
        mock_weaviate.Client.return_value = self.mock_client

        # Mock the SentenceTransformer
        self.mock_model = MagicMock()
        mock_transformer.return_value = self.mock_model

        # Create the search engine
        self.engine = WeaviateSearchEngine(
            host="http://localhost:8080",
            model_name="all-MiniLM-L6-v2",
            articles_class_name="TestArticle",
            statements_class_name="TestStatement",
        )

    def test_initialization(self):
        """Test the initialization of the search engine."""
        # Assert the client was created
        assert self.engine.client is not None
        assert self.engine.articles_class_name == "TestArticle"
        assert self.engine.statements_class_name == "TestStatement"

        # Assert schema was ensured
        assert self.mock_client.schema.create_class.call_count == 2

    @patch("core.infrastructure.search.weaviate_engine.weaviate")
    @patch("core.infrastructure.search.weaviate_engine.SentenceTransformer")
    def test_initialization_failure(self, mock_transformer, mock_weaviate):
        """Test the initialization when Weaviate is not available."""
        # Mock the Weaviate client to fail
        mock_client = MagicMock()
        mock_client.is_ready.return_value = False
        mock_weaviate.Client.return_value = mock_client

        # Create the search engine
        engine = WeaviateSearchEngine()

        # Assert the client is None
        assert engine.client is None

    def test_encode_texts(self):
        """Test the text encoding."""
        # Mock the model encode method
        self.mock_model.encode.return_value = [0.1, 0.2, 0.3]

        # Call the method
        result = self.engine._encode_texts(["test text"])

        # Assert the model was called
        self.mock_model.encode.assert_called_once_with(
            ["test text"], show_progress_bar=False, device="cpu"
        )

        # Assert the result
        assert result == [0.1, 0.2, 0.3]

    def test_add_articles(self):
        """Test adding articles to the search index."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Create a batch context manager mock
        batch_mock = MagicMock()
        self.mock_client.batch.__enter__.return_value = batch_mock

        # Call the method
        articles = [
            {
                "article_id": "123",
                "title": "Test Article",
                "abstract": "This is a test abstract",
            }
        ]
        self.engine.add_articles(articles)

        # Assert the batch was used
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
        """Test adding statements to the search index."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Create a batch context manager mock
        batch_mock = MagicMock()
        self.mock_client.batch.__enter__.return_value = batch_mock

        # Call the method
        statements = [
            {
                "statement_id": "456",
                "text": "Test Statement",
                "abstract": "This is a test abstract",
            }
        ]
        self.engine.add_statements(statements)

        # Assert the batch was used
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
        """Test searching articles."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock the query builder
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        # Mock the query results
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

        # Call the method
        results = self.engine.search_articles("test query", 5)

        # Assert the query was built correctly
        self.mock_client.query.get.assert_called_once_with(
            "TestArticle", ["title", "abstract", "article_id"]
        )
        query_builder.with_near_vector.assert_called_once_with(
            {
                "vector": [0.1, 0.2, 0.3],
            }
        )
        query_builder.with_limit.assert_called_once_with(5)

        # Assert the results
        assert len(results) == 1
        assert results[0]["id"] == "123"
        assert results[0]["item"]["title"] == "Test Article"
        assert results[0]["item"]["abstract"] == "This is a test abstract"
        assert results[0]["score"] == 1.0

    def test_search_statements(self):
        """Test searching statements."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock the query builder
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        # Mock the query results
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

        # Call the method
        results = self.engine.search_statements("test query", 5)

        # Assert the query was built correctly
        self.mock_client.query.get.assert_called_once_with(
            "TestStatement", ["text", "abstract", "statement_id"]
        )
        query_builder.with_near_vector.assert_called_once_with(
            {
                "vector": [0.1, 0.2, 0.3],
            }
        )
        query_builder.with_limit.assert_called_once_with(5)

        # Assert the results
        assert len(results) == 1
        assert results[0]["id"] == "456"
        assert results[0]["item"]["text"] == "Test Statement"
        assert results[0]["item"]["abstract"] == "This is a test abstract"
        assert results[0]["score"] == 1.0

    def test_search_articles_empty_result(self):
        """Test searching articles with empty results."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock the query builder
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        # Mock the query results with empty results
        query_builder.do.return_value = {"data": {"Get": {}}}

        # Call the method
        results = self.engine.search_articles("test query", 5)

        # Assert the results are empty
        assert len(results) == 0

    def test_search_articles_with_invalid_k(self):
        """Test searching articles with an invalid k value."""
        # Mock the encode method
        self.engine._encode_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock the query builder
        query_builder = MagicMock()
        self.mock_client.query.get.return_value = query_builder
        query_builder.with_near_vector.return_value = query_builder
        query_builder.with_limit.return_value = query_builder

        # Mock the query results
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

        # Call the method with an invalid k
        results = self.engine.search_articles("test query", -1)

        # Assert k was changed to the default
        query_builder.with_limit.assert_called_once_with(5)

    def test_delete_indices(self):
        """Test deleting indices."""
        # Call the method
        self.engine.delete_indices()

        # Assert the schema was deleted
        self.mock_client.schema.delete_class.assert_any_call("TestArticle")
        self.mock_client.schema.delete_class.assert_any_call("TestStatement")

        # Assert the schema was recreated
        assert self.mock_client.schema.create_class.call_count >= 2

    def test_client_not_available(self):
        """Test when the client is not available."""
        # Set the client to None
        self.engine.client = None

        # Call the methods
        self.engine.add_articles(
            [{"article_id": "123", "title": "Test", "abstract": "Test"}]
        )
        self.engine.add_statements(
            [{"statement_id": "456", "text": "Test", "abstract": "Test"}]
        )
        results = self.engine.search_articles("test", 5)
        results_statements = self.engine.search_statements("test", 5)
        self.engine.delete_indices()

        # Assert the methods handle the None client gracefully
        assert results == []
        assert results_statements == []
