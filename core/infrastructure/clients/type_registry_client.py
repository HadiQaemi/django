import requests
import logging
from typing import Dict, Any
import uuid
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.application.interfaces.repositories.cache import CacheRepository
from core.domain.exceptions import ExternalServiceError


logger = logging.getLogger(__name__)


class TypeRegistryClient:
    def __init__(
        self,
        cache_repository: CacheRepository,
        base_url: str = "https://typeregistry.lab.pidconsortium.net",
        cache_ttl_days: int = 30,
    ):
        self.base_url = base_url
        self.cache_repository = cache_repository
        self.cache_ttl_days = cache_ttl_days
        # self.session = requests.Session()
        # self.session.headers.update(
        #     {"Accept": "application/json", "User-Agent": "REBORN-API/1.0"}
        # )
        self.session = self._init_session_with_retries()

    def _init_session_with_retries(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_type_info(self, type_id: str) -> Dict[str, Any]:
        cached_data = self.cache_repository.get_schema_by_type_id(type_id)

        if cached_data:
            logger.debug(f"Using cached type information for {type_id}")
            return cached_data, {
                "name": cached_data.name,
                "description": cached_data.description,
                "property": cached_data.property,
            }

        try:
            logger.info(
                f"Fetching type information for {type_id} from external service"
            )
            type_data = self._fetch_from_api(type_id)
            _update_cache = self._update_cache(type_id, type_data)

            properties = []
            for property in type_data["Schema"]["Properties"]:
                properties.append(f"doi:{type_data['Identifier']}#{property['Name']}")
            return _update_cache, {
                "name": type_data["name"].replace("_", " ").capitalize(),
                "property": properties,
                "description": type_data["description"],
            }

        except ExternalServiceError:
            if cached_data:
                logger.warning(
                    f"API call failed for {type_id}, using expired cached data"
                )
                return cached_data.schema_data
            raise

    def _fetch_from_api(self, type_id: str) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}/objects/21.T11969/{type_id}"
            request_id = str(uuid.uuid4())
            headers = {"X-Request-ID": request_id}

            logger.info(f"[{request_id}] Fetching type information from: {url}")

            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            return response.json()
            # url = f"{self.base_url}/objects/21.T11969/{type_id}"
            # logger.info(f"Fetching type information from: {url}")

            # response = self.session.get(url, timeout=30)
            # response.raise_for_status()

            # return response.json()

        except requests.RequestException as e:
            error_message = f"Error fetching type information for {type_id}: {str(e)}"
            logger.error(error_message)
            raise ExternalServiceError(
                service_name="Type Registry",
                error_code=str(getattr(e.response, "status_code", "unknown")),
                message=error_message,
            )
        except ValueError as e:
            error_message = f"Error parsing response for type {type_id}: {str(e)}"
            logger.error(error_message)
            raise ExternalServiceError(
                service_name="Type Registry",
                error_code="PARSE_ERROR",
                message=error_message,
            )

    def _is_cache_valid(self, cached_schema) -> bool:
        if not cached_schema.last_updated:
            return False

        expiration_date = cached_schema.last_updated + timedelta(
            days=self.cache_ttl_days
        )
        return datetime.now() < expiration_date

    def _update_cache(self, type_id: str, type_data: Dict[str, Any]) -> CacheRepository:
        return self.cache_repository.save_schema(type_id, type_data)
