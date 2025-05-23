"""
Integration tests for the paper viewset in the REBORN API.

This module provides integration tests for the paper API endpoints.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.urls import reverse

from core.application.dtos.output_dtos import PaginatedResponseDTO, CommonResponseDTO
from core.presentation.viewsets.paper_viewsets import PaperViewSet
from core.infrastructure.container import Container


@pytest.fixture
def mock_paper_service():
    """Create a mock paper service for testing."""
    service = MagicMock()
    return service


@pytest.mark.django_db
class TestPaperViewSet:
    """Integration tests for the PaperViewSet."""

    def test_list_papers(self, api_client, mock_paper_service, mock_repositories):
        """Test listing all papers."""
        # Mock the paper service
        mock_paper_service.get_all_papers.return_value = PaginatedResponseDTO(
            content=[{"id": "paper1", "title": "Test Paper"}],
            total_elements=1,
            page=1,
            page_size=10,
            total_pages=1,
        )

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:all_paper")
            response = api_client.get(url)

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_elements"] == 1
        assert response.data["page"] == 1
        assert response.data["page_size"] == 10
        assert response.data["total_pages"] == 1
        assert len(response.data["content"]) == 1
        assert response.data["content"][0]["id"] == "paper1"
        assert response.data["content"][0]["title"] == "Test Paper"

        # Verify service call
        mock_paper_service.get_all_papers.assert_called_once_with(1, 10)

    def test_retrieve_paper(self, api_client, mock_paper_service, mock_repositories):
        """Test retrieving a paper by ID."""
        # Mock the paper service
        mock_paper_service.get_paper_by_id.return_value = CommonResponseDTO(
            success=True,
            result={
                "article": {"id": "paper1", "title": "Test Paper"},
                "statements": [{"id": "statement1", "content": "Test Statement"}],
            },
        )

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:paper") + "?id=paper1"
            response = api_client.get(url)

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data["article"]["id"] == "paper1"
        assert response.data["article"]["title"] == "Test Paper"
        assert len(response.data["statements"]) == 1
        assert response.data["statements"][0]["id"] == "statement1"
        assert response.data["statements"][0]["content"] == "Test Statement"

        # Verify service call
        mock_paper_service.get_paper_by_id.assert_called_once_with("paper1")

    def test_retrieve_paper_not_found(
        self, api_client, mock_paper_service, mock_repositories
    ):
        """Test retrieving a non-existent paper."""
        # Mock the paper service
        mock_paper_service.get_paper_by_id.return_value = CommonResponseDTO(
            success=False, message="Paper not found"
        )

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:paper") + "?id=nonexistent"
            response = api_client.get(url)

        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data
        assert response.data["error"] == "Paper not found"

        # Verify service call
        mock_paper_service.get_paper_by_id.assert_called_once_with("nonexistent")

    def test_search_by_title(self, api_client, mock_paper_service, mock_repositories):
        """Test searching papers by title."""
        # Mock the paper service
        mock_paper_service.search_by_title.return_value = [
            {"id": "paper1", "title": "Test Paper"}
        ]

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:search") + "?title=Test"
            response = api_client.get(url)

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_elements"] == 1
        assert len(response.data["content"]) == 1
        assert response.data["content"][0]["id"] == "paper1"
        assert response.data["content"][0]["title"] == "Test Paper"

        # Verify service call
        mock_paper_service.search_by_title.assert_called_once_with("Test")

    def test_query_data(self, api_client, mock_paper_service, mock_repositories):
        """Test querying data with filters."""
        # Mock the paper service
        mock_paper_service.query_data.return_value = CommonResponseDTO(
            success=True,
            result={"paper1": {"id": "paper1", "title": "Test Paper"}},
            total_count=1,
        )

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:filter-statement")
            data = {
                "title": "Test",
                "time_range": {"start": 2023, "end": 2023},
                "authors": ["author1"],
                "journals": ["journal1"],
                "concepts": ["concept1"],
                "conferences": ["conference1"],
                "research_fields": ["rf1"],
                "page": 1,
                "per_page": 10,
            }
            response = api_client.post(url, data=data, format="json")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_elements"] == 1
        assert response.data["page"] == 1
        assert response.data["per_page"] == 10
        assert response.data["total_pages"] == 1
        assert "paper1" in response.data["content"]
        assert response.data["content"]["paper1"]["id"] == "paper1"
        assert response.data["content"]["paper1"]["title"] == "Test Paper"

        # Verify service call
        mock_paper_service.query_data.assert_called_once()

    def test_get_authors(self, api_client, mock_paper_service, mock_repositories):
        """Test getting authors by name."""
        # Mock the paper service
        mock_paper_service.get_authors.return_value = [
            {
                "id": "author1",
                "given_name": "John",
                "family_name": "Doe",
                "label": "John Doe",
            }
        ]

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:get-authors") + "?name=John"
            response = api_client.get(url)

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == "author1"
        assert response.data[0]["name"] == "John Doe"

        # Verify service call
        mock_paper_service.get_authors.assert_called_once_with("John")

    def test_extract_paper(self, api_client, mock_paper_service, mock_repositories):
        """Test extracting a paper from a URL."""
        # Mock the paper service
        mock_paper_service.extract_paper.return_value = CommonResponseDTO(
            success=True, message="Paper extracted successfully"
        )

        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:add-paper")
            data = {"url": "https://example.com"}
            response = api_client.post(url, data=data, format="json")

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.data["result"] is True

        # Verify service call
        mock_paper_service.extract_paper.assert_called_once()

        # Check URL in the call
        args, kwargs = mock_paper_service.extract_paper.call_args
        assert args[0].url == "https://example.com"

    def test_extract_paper_validation_error(
        self, api_client, mock_paper_service, mock_repositories
    ):
        """Test extracting a paper with an invalid URL."""
        # Apply the mock
        with patch.object(
            Container, "get_paper_service", return_value=mock_paper_service
        ):
            # Make API request
            url = reverse("v1:add-paper")
            data = {"url": "invalid-url"}
            response = api_client.post(url, data=data, format="json")

        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

        # Verify service was not called
        mock_paper_service.extract_paper.assert_not_called()
