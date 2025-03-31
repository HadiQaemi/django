"""
Dependency injection container for the REBORN API.

This module provides a dependency injection container for the application.
"""

from typing import Dict, Any, Optional, Type, TypeVar, cast
import importlib
import inspect
import logging
from django.conf import settings

from core.application.interfaces.repositories import (
    PaperRepository,
    StatementRepository,
    AuthorRepository,
    ConceptRepository,
    ResearchFieldRepository,
    JournalRepository,
    SearchRepository,
)
from core.application.interfaces.services import PaperService, SearchService
from core.application.services.paper_service import PaperServiceImpl
from core.application.services.search_service import SearchServiceImpl
from core.infrastructure.repositories.mongo_repos import (
    MongoDBPaperRepository,
    MongoDBStatementRepository,
    MongoDBAuthorRepository,
    MongoDBConceptRepository,
    MongoDBResearchFieldRepository,
    MongoDBJournalRepository,
)
from core.infrastructure.repositories.search_repos import SearchRepositoryImpl

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """Dependency injection container."""

    _instances: Dict[Type, Any] = {}
    _repositories: Dict[Type, Type] = {}
    _services: Dict[Type, Type] = {}

    @classmethod
    def configure(cls) -> None:
        """Configure the container based on settings."""
        # Repository mapping
        cls._repositories = {
            PaperRepository: MongoDBPaperRepository,
            StatementRepository: MongoDBStatementRepository,
            AuthorRepository: MongoDBAuthorRepository,
            ConceptRepository: MongoDBConceptRepository,
            ResearchFieldRepository: MongoDBResearchFieldRepository,
            JournalRepository: MongoDBJournalRepository,
            SearchRepository: SearchRepositoryImpl,
        }

        # Service mapping
        cls._services = {
            PaperService: PaperServiceImpl,
            SearchService: SearchServiceImpl,
        }

        # Database-specific repositories
        db_type = getattr(settings, "DATABASE_TYPE", "mongodb")
        if db_type == "postgresql":
            try:
                # Import SQL repositories
                from core.infrastructure.repositories.sql_repos import (
                    SQLPaperRepository,
                    SQLStatementRepository,
                    SQLAuthorRepository,
                    SQLConceptRepository,
                    SQLResearchFieldRepository,
                    SQLJournalRepository,
                )

                # Update repository mapping
                cls._repositories.update(
                    {
                        PaperRepository: SQLPaperRepository,
                        StatementRepository: SQLStatementRepository,
                        AuthorRepository: SQLAuthorRepository,
                        ConceptRepository: SQLConceptRepository,
                        ResearchFieldRepository: SQLResearchFieldRepository,
                        JournalRepository: SQLJournalRepository,
                    }
                )

                logger.info("Using PostgreSQL repositories")
            except ImportError:
                logger.warning(
                    "SQL repositories not available, falling back to MongoDB"
                )
        else:
            logger.info("Using MongoDB repositories")

    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """Resolve a dependency by interface."""
        if not cls._repositories or not cls._services:
            cls.configure()

        # Check if instance already exists
        if interface in cls._instances:
            return cast(T, cls._instances[interface])

        implementation = None

        # Get implementation from repository mapping
        if interface in cls._repositories:
            implementation = cls._repositories[interface]

        # Get implementation from service mapping
        elif interface in cls._services:
            implementation = cls._services[interface]

        if not implementation:
            raise ValueError(f"No implementation found for {interface}")

        # Check if implementation requires dependencies
        try:
            if hasattr(implementation, "__init__"):
                init_signature = inspect.signature(implementation.__init__)
                params = {
                    name: cls.resolve(param.annotation)
                    for name, param in init_signature.parameters.items()
                    if name != "self"
                    and param.annotation != inspect.Parameter.empty
                    and param.default == inspect.Parameter.empty
                }
                instance = implementation(**params)
            else:
                instance = implementation()

            cls._instances[interface] = instance
            return cast(T, instance)

        except Exception as e:
            logger.error(f"Error resolving {interface}: {str(e)}")
            raise

    @classmethod
    def reset(cls) -> None:
        """Reset the container."""
        cls._instances = {}

    @classmethod
    def get_paper_service(cls) -> PaperService:
        """Get the paper service."""
        return cls.resolve(PaperService)

    @classmethod
    def get_search_service(cls) -> SearchService:
        """Get the search service."""
        return cls.resolve(SearchService)
