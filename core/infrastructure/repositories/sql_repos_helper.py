import logging
import hashlib

logger = logging.getLogger(__name__)


def generate_static_id(input_string: str) -> str:
    """Generate a static ID from a string."""
    hash_object = hashlib.sha256(input_string.encode("utf-8"))
    return hash_object.hexdigest()[:32]


def fetch_reborn_doi(doi: str) -> str:
    """Fetch the reborn DOI from a regular DOI."""
    import requests

    url = "https://api.datacite.org/dois"
    query = f'relatedIdentifiers.relatedIdentifier:"{doi.replace("https://doi.org/", "")}" AND relatedIdentifiers.relationType:IsVariantFormOf'
    params = {"query": query}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("data"):
            return ""

        return f"https://doi.org/{result['data'][0]['id']}"

    except Exception as e:
        logger.error(f"Error fetching reborn DOI: {str(e)}")
        return ""
