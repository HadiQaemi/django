import os
import logging
import hashlib
import re
from django.core.files.base import ContentFile
from django.conf import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def generate_static_id(input_string: str) -> str:
    """Generate a static ID from a string."""
    hash_object = hashlib.sha256(input_string.encode("utf-8"))
    return hash_object.hexdigest()[:32]


def is_orcid_url(s: str) -> bool:
    try:
        result = urlparse(s)
        if not all([result.scheme in ("http", "https"), result.netloc]):
            return False
    except Exception as e:
        logger.error(f"Error fetching reborn DOI: {str(e)}")
        return False

    orcid_pattern = re.compile(r"^https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
    return bool(orcid_pattern.match(s))


def articlet_ro_crate_upload_path(instance, filename):
    if instance and instance.article_id:
        return f"files/{instance.article_id}/{filename}"
    else:
        return f"files/no_digital_objects/{filename}"


def process_source_code_content_flexible(content_file, filename, article_id=None):
    try:
        content_file.seek(0)
        content = content_file.read()

        try:
            if isinstance(content, bytes):
                text_content = content.decode("utf-8")
            else:
                text_content = content

            csv_link_pattern = r'https://service.tib.eu/[^"\s]*\.csv'

            def replace_csv_link(match):
                original_url = match.group(0)
                csv_filename = os.path.basename(original_url)
                domain_url = getattr(
                    settings,
                    "DOMAIN_URL",
                    os.environ.get("DOMAIN_URL", "https://reborn.orkg.org"),
                )
                domain_url = domain_url.rstrip("/")
                if article_id:
                    new_url = f"{domain_url}{settings.MEDIA_URL}files/{article_id}/{csv_filename}"
                else:
                    new_url = f"{domain_url}{settings.MEDIA_URL}files/{csv_filename}"
                return new_url

            modified_content = re.sub(csv_link_pattern, replace_csv_link, text_content)

            if modified_content != text_content:
                print(f"Modified {filename} - replaced CSV links")
                if isinstance(content, bytes):
                    modified_content = modified_content.encode("utf-8")
                return ContentFile(modified_content, name=filename)

        except Exception as e:
            print(f"Error processing content: {e}")

    except Exception as e:
        print(f"Error: {e}")

    content_file.seek(0)
    return content_file


def fetch_reborn_doi(doi: str) -> str:
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
