import os
import pytest
from typing import Dict, Any, List, Generator
import mongomock
import fakeredis
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient

from django.conf import settings

from core.infrastructure.container import Container
from core.application.interfaces.repositories import (
    PaperRepository,
    StatementRepository,
    AuthorRepository,
    ConceptRepository,
    ResearchFieldRepository,
    JournalRepository,
    SearchRepository,
)
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


@pytest.fixture(scope="session", autouse=True)
def setup_django_settings():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


@pytest.fixture(scope="function")
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="function")
def mock_mongo_client() -> mongomock.MongoClient:
    return mongomock.MongoClient()


@pytest.fixture(scope="function")
def mock_redis_client() -> fakeredis.FakeStrictRedis:
    return fakeredis.FakeStrictRedis()


@pytest.fixture(scope="function")
def mock_elasticsearch_client() -> MagicMock:
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.indices.exists.return_value = True
    mock_client.indices.create.return_value = {"acknowledged": True}
    mock_client.indices.delete.return_value = {"acknowledged": True}
    mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
    return mock_client


@pytest.fixture(scope="function")
def mock_repositories(
    mock_mongo_client: mongomock.MongoClient,
) -> Generator[None, None, None]:
    db = mock_mongo_client["test_db"]

    mock_paper_repo = MagicMock(spec=PaperRepository)
    mock_statement_repo = MagicMock(spec=StatementRepository)
    mock_author_repo = MagicMock(spec=AuthorRepository)
    mock_concept_repo = MagicMock(spec=ConceptRepository)
    mock_research_field_repo = MagicMock(spec=ResearchFieldRepository)
    mock_journal_repo = MagicMock(spec=JournalRepository)
    mock_search_repo = MagicMock(spec=SearchRepository)

    mock_paper_repo.find_all.return_value = ([], 0)
    mock_statement_repo.find_all.return_value = ([], 0)

    original_resolve = Container.resolve

    def mock_resolve(interface):
        if interface == PaperRepository:
            return mock_paper_repo
        elif interface == StatementRepository:
            return mock_statement_repo
        elif interface == AuthorRepository:
            return mock_author_repo
        elif interface == ConceptRepository:
            return mock_concept_repo
        elif interface == ResearchFieldRepository:
            return mock_research_field_repo
        elif interface == JournalRepository:
            return mock_journal_repo
        elif interface == SearchRepository:
            return mock_search_repo
        else:
            return original_resolve(interface)

    with patch.object(Container, "resolve", side_effect=mock_resolve):
        yield

    Container.reset()


@pytest.fixture(scope="function")
def sample_author() -> Author:
    return Author(id="author1", given_name="John", family_name="Doe", label="John Doe")


@pytest.fixture(scope="function")
def sample_concept() -> Concept:
    return Concept(id="concept1", label="Machine Learning", identifier="ML001")


@pytest.fixture(scope="function")
def sample_research_field() -> ResearchField:
    return ResearchField(id="rf1", label="Computer Science")


@pytest.fixture(scope="function")
def sample_statement(sample_author: Author) -> Statement:
    return Statement(
        id="statement1",
        content={"key": "value"},
        author=[sample_author],
        article_id="paper1",
        statement_id="statement1",
        supports=[{"notation": {"label": "This is a test statement"}}],
    )


@pytest.fixture(scope="function")
def sample_paper(sample_author: Author, sample_research_field: ResearchField) -> Article:
    return Article(
        id="paper1",
        title="Test Paper",
        author=[sample_author],
        abstract="This is a test abstract",
        article_id="paper1",
        research_fields=[sample_research_field],
        research_fields_id=["rf1"],
    )
