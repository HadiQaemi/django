import os
import requests
from bs4 import BeautifulSoup
import time
import uuid
from collections import defaultdict
import logging
from typing import Dict, Any, Optional
import json
import mimetypes
from urllib.parse import urlparse
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)
mimetypes.add_type("application/x-python", ".py")
mimetypes.add_type("text/x-r", ".r")


class NodeExtractor:
    def __init__(self):
        self.url = ""
        self.metadata = ""
        self.soup = None
        self.doi = ""
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }
        )

    def set_url(self, url: str) -> None:
        self.url = url
        self.soup = None
        self.doi = ""
        self.metadata = ""

    def fetch_html(self) -> None:
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch HTML: {str(e)}")
            raise Exception(f"Failed to fetch HTML: {str(e)}")

    def get_file_content_and_type(
        self, url, max_size_mb=20, allowed_domain="service.tib.eu"
    ):
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not parsed_url.netloc.endswith(allowed_domain):
            print(f"Blocked download from unauthorized domain: {parsed_url.netloc}")
            print(f"Only downloads from {allowed_domain} are allowed")
            return filename, None, None, False, 0

        if parsed_url.scheme != "https":
            print(f"Blocked non-HTTPS URL: {url}")
            print("Only HTTPS URLs are allowed")
            return filename, None, None, False, 0

        mime_type, _ = mimetypes.guess_type(filename)

        if not mime_type:
            if filename.endswith(".zip"):
                mime_type = "application/zip"
            elif filename.endswith(".csv"):
                mime_type = "text/csv"
            elif filename.endswith(".json"):
                mime_type = "application/json"
            else:
                mime_type = "application/octet-stream"

        max_size_bytes = max_size_mb * 1024 * 1024

        try:
            head_response = requests.head(url, allow_redirects=True, timeout=10)
            content_length = head_response.headers.get("Content-Length")

            if content_length:
                file_size = int(content_length)
                file_size_mb = file_size / (1024 * 1024)

                if file_size > max_size_bytes:
                    # File is too large, return metadata only
                    print(
                        f"File {filename} is {file_size_mb:.2f}MB, exceeds {max_size_mb}MB limit"
                    )
                    return filename, None, mime_type, True, file_size_mb
        except Exception as e:
            print(f"Could not check file size via HEAD request: {e}")

        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Failed to download file from URL: {url}")

            content_length = response.headers.get("Content-Length")
            if content_length:
                file_size = int(content_length)
                file_size_mb = file_size / (1024 * 1024)

                if file_size > max_size_bytes:
                    print(
                        f"File {filename} is {file_size_mb:.2f}MB, exceeds {max_size_mb}MB limit"
                    )
                    return filename, None, mime_type, True, file_size_mb

            downloaded_size = 0
            chunks = []

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size_bytes:
                        file_size_mb = downloaded_size / (1024 * 1024)
                        print(
                            f"File {filename} exceeded {max_size_mb}MB limit during download ({file_size_mb:.2f}MB)"
                        )
                        return filename, None, mime_type, True, file_size_mb
                    chunks.append(chunk)

            content = b"".join(chunks)
            file_size_mb = downloaded_size / (1024 * 1024)
            content_file = ContentFile(content, name=filename)
            print(f"Successfully downloaded {filename} ({file_size_mb:.2f}MB)")
            return filename, content_file, mime_type, False, file_size_mb

        except Exception as e:
            print(f"Error downloading file {filename}: {e}")
            raise

    def all_json_files(self) -> Dict[str, str]:
        if not self.soup:
            self.fetch_html()

        try:
            heading = self.soup.find("section", id="dataset-resources").find_all(
                "a", class_="heading"
            )
            json_links = defaultdict(str)

            for item in heading:
                span = item.find("span", class_="format-label")
                if span and span.get("data-format") == "json":
                    url = (
                        "https://service.tib.eu/"
                        + item["href"]
                        + "/download/"
                        + item["title"]
                    )
                    json_links[item["title"]] = url

            return json_links

        except Exception as e:
            logger.error(f"Error extracting JSON files: {str(e)}")
            raise Exception(f"Error extracting JSON files: {str(e)}")

    def load_json_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            json_data = response.json()
            json_data["_id"] = self.generate_timestamp_based_id()

            return json_data

        except requests.RequestException as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            return None

    def generate_timestamp_based_id(self) -> str:
        timestamp = int(time.time() * 1000)
        random_part = str(uuid.uuid4())[:8]
        unique_id = f"{timestamp}_{random_part}"
        return unique_id

    def extract_metadata(self) -> Dict[str, Any]:
        if not self.soup:
            self.fetch_html()

        try:
            metadata = {}
            title_element = self.soup.find("h1", class_="page-heading")
            if title_element:
                metadata["title"] = title_element.text.strip()

            description_element = self.soup.find("div", class_="dataset-notes")
            if description_element:
                metadata["description"] = description_element.text.strip()

            doi_element = self.soup.find("span", class_="doi")
            if doi_element:
                self.doi = doi_element.text.strip()
                metadata["doi"] = self.doi

            authors_element = self.soup.find("div", class_="dataset-authors")
            if authors_element:
                authors = []
                author_elements = authors_element.find_all("a")
                for author_element in author_elements:
                    authors.append(author_element.text.strip())
                metadata["authors"] = authors

            tags_element = self.soup.find("ul", class_="tag-list")
            if tags_element:
                tags = []
                tag_elements = tags_element.find_all("li")
                for tag_element in tag_elements:
                    tag_link = tag_element.find("a")
                    if tag_link:
                        tags.append(tag_link.text.strip())
                metadata["tags"] = tags

            additional_metadata = {}
            metadata_elements = self.soup.find_all("tr", class_="dataset-details")
            for element in metadata_elements:
                key_element = element.find("th")
                value_element = element.find("td")
                if key_element and value_element:
                    key = key_element.text.strip()
                    value = value_element.text.strip()
                    additional_metadata[key] = value

            metadata["additional_metadata"] = additional_metadata

            self.metadata = metadata
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise Exception(f"Error extracting metadata: {str(e)}")
