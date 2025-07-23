from typing import Dict, Any, Type, TypeVar, cast
import inspect
import logging
from django.conf import settings

from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.cache import CacheRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.repositories.search import SearchRepository
from core.application.interfaces.repositories.statement import StatementRepository
from core.application.interfaces.services.auto_complete import AutoCompleteService
from core.application.interfaces.services.insight import InsightService
from core.application.interfaces.services.paper import PaperService
from core.application.services.paper_service import PaperServiceImpl
from core.application.services.auto_complete_service import AutoCompleteServiceImpl
from core.application.services.insight_service import InsightServiceImpl

from core.infrastructure.clients.type_registry_client import TypeRegistryClient
from core.infrastructure.repositories.search_repos import SearchRepositoryImpl
from core.infrastructure.repositories.sql_repos.author import SQLAuthorRepository
from core.infrastructure.repositories.sql_repos.concept import SQLConceptRepository
from core.infrastructure.repositories.sql_repos.journal import SQLJournalRepository
from core.infrastructure.repositories.sql_repos.paper import SQLPaperRepository
from core.infrastructure.repositories.sql_repos.research_field import (
    SQLResearchFieldRepository,
)
from core.infrastructure.repositories.sql_repos.statement import SQLStatementRepository
from core.infrastructure.repositories.cache_repos import SQLCacheRepository

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
        cls._repositories = {
            PaperRepository: SQLPaperRepository,
            StatementRepository: SQLStatementRepository,
            AuthorRepository: SQLAuthorRepository,
            ConceptRepository: SQLConceptRepository,
            ResearchFieldRepository: SQLResearchFieldRepository,
            JournalRepository: SQLJournalRepository,
            CacheRepository: SQLCacheRepository,
            SearchRepository: SearchRepositoryImpl,
        }

        cls._services = {
            PaperService: PaperServiceImpl,
            AutoCompleteService: AutoCompleteServiceImpl,
            InsightService: InsightServiceImpl,
        }
        db_type = getattr(settings, "DATABASE_TYPE", "postgres")
        print("--------db_type--------")
        print(db_type)
        if db_type == "postgres":
            try:
                cls._repositories.update(
                    {
                        PaperRepository: SQLPaperRepository,
                        StatementRepository: SQLStatementRepository,
                        AuthorRepository: SQLAuthorRepository,
                        ConceptRepository: SQLConceptRepository,
                        ResearchFieldRepository: SQLResearchFieldRepository,
                        JournalRepository: SQLJournalRepository,
                        CacheRepository: SQLCacheRepository,
                    }
                )

                logger.info("Using PostgreSQL repositories")
            except ImportError:
                logger.warning(
                    "SQL repositories not available, falling back to MongoDB"
                )
        else:
            logger.info("Using MongoDB repositories")
        cache_repo = cls.resolve(CacheRepository)
        cls._instances[TypeRegistryClient] = TypeRegistryClient(cache_repo)

    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """Resolve a dependency by interface."""
        if not cls._repositories or not cls._services:
            cls.configure()

        if interface in cls._instances:
            return cast(T, cls._instances[interface])
        implementation = None

        if interface in cls._repositories:
            implementation = cls._repositories[interface]
        elif interface in cls._services:
            implementation = cls._services[interface]

        if not implementation:
            raise ValueError(f"No implementation found for {interface}")

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
    def get_auto_complete_service(cls) -> AutoCompleteService:
        """Get the auto-complete service."""
        return cls.resolve(AutoCompleteService)

    @classmethod
    def get_insight_service(cls) -> InsightService:
        """Get the insight service."""
        return cls.resolve(InsightService)
