"""
Tests for domain entities in the REBORN API.

This module provides unit tests for domain entities.
"""

import pytest
from datetime import datetime

from core.domain.entities import (
    Article,
    Statement,
    Author,
    Concept,
    ResearchField,
    Journal,
    Conference,
    Notation,
    Contribution,
)


class TestAuthor:
    """Tests for the Author entity."""

    def test_init(self):
        """Test Author initialization."""
        author = Author(
            id="author1", given_name="John", family_name="Doe", label="John Doe"
        )

        assert author.id == "author1"
        assert author.given_name == "John"
        assert author.family_name == "Doe"
        assert author.label == "John Doe"

    def test_full_name(self):
        """Test Author full_name property."""
        author = Author(id="author1", given_name="John", family_name="Doe", label=None)

        assert author.full_name == "John Doe"


class TestConcept:
    """Tests for the Concept entity."""

    def test_init(self):
        """Test Concept initialization."""
        concept = Concept(id="concept1", label="Machine Learning", identifier="ML001")

        assert concept.id == "concept1"
        assert concept.label == "Machine Learning"
        assert concept.identifier == "ML001"


class TestResearchField:
    """Tests for the ResearchField entity."""

    def test_init(self):
        """Test ResearchField initialization."""
        research_field = ResearchField(id="rf1", label="Computer Science")

        assert research_field.id == "rf1"
        assert research_field.label == "Computer Science"


class TestNotation:
    """Tests for the Notation entity."""

    def test_init(self):
        """Test Notation initialization."""
        concept = Concept(id="concept1", label="Machine Learning", identifier="ML001")

        notation = Notation(
            id="notation1", label="This is a test notation", concept=concept
        )

        assert notation.id == "notation1"
        assert notation.label == "This is a test notation"
        assert notation.concept == concept


class TestStatement:
    """Tests for the Statement entity."""

    def test_init(self):
        """Test Statement initialization."""
        author = Author(
            id="author1", given_name="John", family_name="Doe", label="John Doe"
        )

        statement = Statement(
            id="statement1",
            content={"key": "value"},
            author=[author],
            article_id="paper1",
            statement_id="statement1",
            supports=[{"notation": {"label": "This is a test statement"}}],
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2),
        )

        assert statement.id == "statement1"
        assert statement.content == {"key": "value"}
        assert statement.author == [author]
        assert statement.article_id == "paper1"
        assert statement.statement_id == "statement1"
        assert statement.supports == [
            {"notation": {"label": "This is a test statement"}}
        ]
        assert statement.created_at == datetime(2023, 1, 1)
        assert statement.updated_at == datetime(2023, 1, 2)


class TestContribution:
    """Tests for the Contribution entity."""

    def test_init(self):
        """Test Contribution initialization."""
        author = Author(
            id="author1", given_name="John", family_name="Doe", label="John Doe"
        )

        contribution = Contribution(
            id="contribution1",
            title="Test Contribution",
            author=[author],
            info={"key": "value"},
            paper_id="paper1",
            json_id="json1",
            json_type="type1",
            json_context={"context": "value"},
            predicates={"predicate1": "value1"},
        )

        assert contribution.id == "contribution1"
        assert contribution.title == "Test Contribution"
        assert contribution.author == [author]
        assert contribution.info == {"key": "value"}
        assert contribution.paper_id == "paper1"
        assert contribution.json_id == "json1"
        assert contribution.json_type == "type1"
        assert contribution.json_context == {"context": "value"}
        assert contribution.predicates == {"predicate1": "value1"}


class TestPaper:
    """Tests for the Paper entity."""

    def test_init(self):
        """Test Paper initialization."""
        author = Author(
            id="author1", given_name="John", family_name="Doe", label="John Doe"
        )

        research_field = ResearchField(id="rf1", label="Computer Science")

        journal = Journal(
            id="journal1", label="Test Journal", publisher={"name": "Test Publisher"}
        )

        statement = Statement(
            id="statement1",
            content={"key": "value"},
            author=[author],
            article_id="paper1",
            statement_id="statement1",
            supports=[{"notation": {"label": "This is a test statement"}}],
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2),
        )

        contribution = Contribution(
            id="contribution1",
            title="Test Contribution",
            author=[author],
            info={"key": "value"},
            paper_id="paper1",
            json_id="json1",
            json_type="type1",
            json_context={"context": "value"},
            predicates={"predicate1": "value1"},
        )

        concept = Concept(id="concept1", label="Machine Learning", identifier="ML001")

        paper = Article(
            id="paper1",
            title="Test Paper",
            author=[author],
            abstract="This is a test abstract",
            contributions=[contribution],
            statements=[statement],
            dois="10.1234/test",
            date_published=datetime(2023, 1, 1),
            entity="entity1",
            external="https://example.com",
            info={"key": "value"},
            timeline={"published": "2023-01-01"},
            journal=journal,
            conference=None,
            publisher={"name": "Test Publisher"},
            research_fields=[research_field],
            research_fields_id=["rf1"],
            article_id="paper1",
            reborn_doi="10.5678/reborn",
            paper_type="research",
            concepts=[concept],
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 2),
        )

        assert paper.id == "paper1"
        assert paper.title == "Test Paper"
        assert paper.author == [author]
        assert paper.abstract == "This is a test abstract"
        assert paper.contributions == [contribution]
        assert paper.statements == [statement]
        assert paper.dois == "10.1234/test"
        assert paper.date_published == datetime(2023, 1, 1)
        assert paper.entity == "entity1"
        assert paper.external == "https://example.com"
        assert paper.info == {"key": "value"}
        assert paper.timeline == {"published": "2023-01-01"}
        assert paper.journal == journal
        assert paper.conference is None
        assert paper.publisher == {"name": "Test Publisher"}
        assert paper.research_fields == [research_field]
        assert paper.research_fields_id == ["rf1"]
        assert paper.article_id == "paper1"
        assert paper.reborn_doi == "10.5678/reborn"
        assert paper.paper_type == "research"
        assert paper.concepts == [concept]
        assert paper.created_at == datetime(2023, 1, 1)
        assert paper.updated_at == datetime(2023, 1, 2)
