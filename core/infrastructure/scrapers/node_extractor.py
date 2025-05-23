"""
Web scraper for extracting data from web pages.

This module implements a web scraper for extracting data from web pages,
particularly for the REBORN API.
"""

import requests
from bs4 import BeautifulSoup
import time
import uuid
from collections import defaultdict
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class NodeExtractor:
    """Web scraper for extracting data from web pages."""

    def __init__(self):
        """Initialize the scraper."""
        self.url = ""
        self.metadata = ""
        self.soup = None
        self.doi = ""
        self.session = requests.Session()

        # Set up headers to mimic a browser request
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
        """Set the URL to scrape."""
        self.url = url
        self.soup = None
        self.doi = ""
        self.metadata = ""

    def fetch_html(self) -> None:
        """Fetch the HTML content of the URL."""
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch HTML: {str(e)}")
            raise Exception(f"Failed to fetch HTML: {str(e)}")

    def all_json_files(self) -> Dict[str, str]:
        """Get all JSON files from the web page."""
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
                    # url = (
                    #     "http://localhost/data/baimuratov-2024-2/"
                    #     + item["title"]
                    # )
                    # print(url)
                    # print(item)
                    json_links[item["title"]] = url

            return json_links

        except Exception as e:
            logger.error(f"Error extracting JSON files: {str(e)}")
            raise Exception(f"Error extracting JSON files: {str(e)}")

    def load_json_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Load JSON from a URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse JSON
            json_data = response.json()

            # Add a unique ID to the JSON data
            json_data["_id"] = self.generate_timestamp_based_id()

            return json_data

        except requests.RequestException as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            return None

    def generate_timestamp_based_id(self) -> str:
        """Generate a timestamp-based ID."""
        timestamp = int(time.time() * 1000)
        random_part = str(uuid.uuid4())[:8]
        unique_id = f"{timestamp}_{random_part}"
        return unique_id

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the web page."""
        if not self.soup:
            self.fetch_html()

        try:
            metadata = {}

            # Extract title
            title_element = self.soup.find("h1", class_="page-heading")
            if title_element:
                metadata["title"] = title_element.text.strip()

            # Extract description
            description_element = self.soup.find("div", class_="dataset-notes")
            if description_element:
                metadata["description"] = description_element.text.strip()

            # Extract DOI
            doi_element = self.soup.find("span", class_="doi")
            if doi_element:
                self.doi = doi_element.text.strip()
                metadata["doi"] = self.doi

            # Extract authors
            authors_element = self.soup.find("div", class_="dataset-authors")
            if authors_element:
                authors = []
                author_elements = authors_element.find_all("a")
                for author_element in author_elements:
                    authors.append(author_element.text.strip())
                metadata["authors"] = authors

            # Extract tags
            tags_element = self.soup.find("ul", class_="tag-list")
            if tags_element:
                tags = []
                tag_elements = tags_element.find_all("li")
                for tag_element in tag_elements:
                    tag_link = tag_element.find("a")
                    if tag_link:
                        tags.append(tag_link.text.strip())
                metadata["tags"] = tags

            # Extract additional metadata
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
