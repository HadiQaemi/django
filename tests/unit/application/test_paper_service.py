"""
Tests for the paper service in the REBORN API.

This module provides unit tests for the paper service.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from core.application.services.paper_service import PaperServiceImpl
from core.application.dtos.input_dtos import QueryFilterInputDTO, ScraperUrlInputDTO
from core.application.dtos.output_dtos import (
    PaperOutputDTO,
    StatementOutputDTO,
    PaginatedResponseDTO,
    CommonResponseDTO,
)
from core.domain.entities import Paper, Statement, Author, Concept, ResearchField
from core.domain.exceptions import EntityNotFound, DatabaseError


@pytest.fixture
def mock_repositories():
    """Create mock repositories for testing."""
    paper_repo = MagicMock()
    statement_repo = MagicMock()
    author_repo = MagicMock()
    concept_repo = MagicMock()
    research_field_repo = MagicMock()
    journal_repo = MagicMock()

    return (
        paper_repo,
        statement_repo,
        author_repo,
        concept_repo,
        research_field_repo,
        journal_repo,
    )


@pytest.fixture
def paper_service(mock_repositories):
    """Create a paper service instance for testing."""
    (
        paper_repo,
        statement_repo,
        author_repo,
        concept_repo,
        research_field_repo,
        journal_repo,
    ) = mock_repositories

    service = PaperServiceImpl(
        paper_repository=paper_repo,
        statement_repository=statement_repo,
        author_repository=author_repo,
        concept_repository=concept_repo,
        research_field_repository=research_field_repo,
        journal_repository=journal_repo,
    )

    return service


class TestPaperService:
    """Tests for the paper service."""

    def test_get_all_papers(self, paper_service, mock_repositories, sample_paper):
        """Test get_all_papers method."""
        paper_repo = mock_repositories[0]
        paper_repo.find_all.return_value = ([sample_paper], 1)

        result = paper_service.get_all_papers(page=1, page_size=10)

        assert isinstance(result, PaginatedResponseDTO)
        assert result.total_elements == 1
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1
        assert len(result.content) == 1
        assert result.content[0].id == sample_paper.id
        assert result.content[0].title == sample_paper.title

        paper_repo.find_all.assert_called_once_with(1, 10)

    def test_get_paper_by_id_success(
        self, paper_service, mock_repositories, sample_paper, sample_statement
    ):
        """Test get_paper_by_id method with a successful result."""
        paper_repo = mock_repositories[0]
        statement_repo = mock_repositories[1]

        paper_repo.find_by_id.return_value = sample_paper
        statement_repo.find_by_paper_id.return_value = [sample_statement]

        result = paper_service.get_paper_by_id("paper1")

        assert isinstance(result, CommonResponseDTO)
        assert result.success is True
        assert "article" in result.result
        assert "statements" in result.result
        assert result.result["article"].id == sample_paper.id
        assert result.result["article"].title == sample_paper.title
        assert len(result.result["statements"]) == 1
        assert result.result["statements"][0].id == sample_statement.id

        paper_repo.find_by_id.assert_called_once_with("paper1")
        statement_repo.find_by_paper_id.assert_called_once_with("paper1")

    def test_get_paper_by_id_not_found(self, paper_service, mock_repositories):
        """Test get_paper_by_id method with a not found result."""
        paper_repo = mock_repositories[0]
        paper_repo.find_by_id.return_value = None

        result = paper_service.get_paper_by_id("nonexistent")

        assert isinstance(result, CommonResponseDTO)
        assert result.success is False
        assert "not found" in result.message.lower()

        paper_repo.find_by_id.assert_called_once_with("nonexistent")

    def test_get_all_statements(
        self, paper_service, mock_repositories, sample_statement
    ):
        """Test get_all_statements method."""
        statement_repo = mock_repositories[1]
        statement_repo.find_all.return_value = ([sample_statement], 1)

        result = paper_service.get_all_statements(page=1, page_size=10)

        assert isinstance(result, PaginatedResponseDTO)
        assert result.total_elements == 1
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1
        assert len(result.content) == 1
        assert result.content[0].id == sample_statement.id

        statement_repo.find_all.assert_called_once_with(1, 10)

    def test_search_by_title(self, paper_service, mock_repositories, sample_paper):
        """Test search_by_title method."""
        paper_repo = mock_repositories[0]
        paper_repo.search_by_title.return_value = [sample_paper]

        result = paper_service.search_by_title("Test")

        assert len(result) == 1
        assert result[0].id == sample_paper.id
        assert result[0].title == sample_paper.title

        paper_repo.search_by_title.assert_called_once_with("Test")

    def test_query_data(self, paper_service, mock_repositories, sample_paper):
        """Test query_data method."""
        paper_repo = mock_repositories[0]
        paper_repo.query_papers.return_value = ([sample_paper], 1)

        filter_dto = QueryFilterInputDTO(
            title="Test",
            start_year=2023,
            end_year=2023,
            author_ids=["author1"],
            journal_names=["journal1"],
            concept_ids=["concept1"],
            conference_names=["conference1"],
            research_fields=["rf1"],
            page=1,
            per_page=10,
        )

        result = paper_service.query_data(filter_dto)

        assert isinstance(result, CommonResponseDTO)
        assert result.success is True
        assert result.total_count == 1
        assert sample_paper.id in result.result

        paper_repo.query_papers.assert_called_once_with(
            start_year=2023,
            end_year=2023,
            author_ids=["author1"],
            journal_names=["journal1"],
            concept_ids=["concept1"],
            conference_names=["conference1"],
            title="Test",
            research_fields=["rf1"],
            page=1,
            page_size=10,
        )

    def test_get_statement_by_id(
        self, paper_service, mock_repositories, sample_statement
    ):
        """Test get_statement_by_id method."""
        statement_repo = mock_repositories[1]
        statement_repo.find_by_id.return_value = sample_statement

        result = paper_service.get_statement_by_id("statement1")

        assert isinstance(result, CommonResponseDTO)
        assert result.success is True
        assert "statement" in result.result
        assert result.result["statement"].id == sample_statement.id

        statement_repo.find_by_id.assert_called_once_with("statement1")

    def test_get_authors(self, paper_service, mock_repositories, sample_author):
        """Test get_authors method."""
        author_repo = mock_repositories[2]
        author_repo.find_by_name.return_value = [sample_author]

        result = paper_service.get_authors("John")

        assert len(result) == 1
        assert result[0].id == sample_author.id
        assert result[0].given_name == sample_author.given_name
        assert result[0].family_name == sample_author.family_name

        author_repo.find_by_name.assert_called_once_with("John")

    def test_get_concepts(self, paper_service, mock_repositories, sample_concept):
        """Test get_concepts method."""
        concept_repo = mock_repositories[3]
        concept_repo.find_by_label.return_value = [sample_concept]

        result = paper_service.get_concepts("Machine")

        assert len(result) == 1
        assert result[0].id == sample_concept.id
        assert result[0].label == sample_concept.label

        concept_repo.find_by_label.assert_called_once_with("Machine")

    def test_get_latest_concepts(
        self, paper_service, mock_repositories, sample_concept
    ):
        """Test get_latest_concepts method."""
        concept_repo = mock_repositories[3]
        concept_repo.get_latest_concepts.return_value = [sample_concept]

        result = paper_service.get_latest_concepts()

        assert len(result) == 1
        assert result[0].id == sample_concept.id
        assert result[0].label == sample_concept.label

        concept_repo.get_latest_concepts.assert_called_once()

    def test_extract_paper(self, paper_service, mock_repositories):
        """Test extract_paper method."""
        paper_repo = mock_repositories[0]
        paper_repo.add_article.return_value = True

        url_dto = ScraperUrlInputDTO(url="https://example.com")

        # Mock scraper methods
        paper_service.scraper.set_url = MagicMock()
        paper_service.scraper.all_json_files = MagicMock(
            return_value={"ro-crate-metadata.json": "url1"}
        )
        paper_service.scraper.load_json_from_url = MagicMock(
            return_value={"key": "value"}
        )

        result = paper_service.extract_paper(url_dto)

        assert isinstance(result, CommonResponseDTO)
        assert result.success is True

        paper_service.scraper.set_url.assert_called_once_with("https://example.com")
        paper_service.scraper.all_json_files.assert_called_once()
        paper_service.scraper.load_json_from_url.assert_called_once()
        paper_repo.add_article.assert_called_once()

    def test_delete_database(self, paper_service, mock_repositories):
        """Test delete_database method."""
        paper_repo = mock_repositories[0]
        paper_repo.delete_database.return_value = True

        result = paper_service.delete_database()

        assert isinstance(result, CommonResponseDTO)
        assert result.success is True

        paper_repo.delete_database.assert_called_once()

    def test_error_handling(self, paper_service, mock_repositories):
        """Test error handling in the service."""
        paper_repo = mock_repositories[0]
        paper_repo.find_all.side_effect = DatabaseError("Test error")

        with pytest.raises(DatabaseError) as excinfo:
            paper_service.get_all_papers(page=1, page_size=10)

        assert "Test error" in str(excinfo.value)
