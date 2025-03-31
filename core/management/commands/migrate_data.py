"""
Command for data migration in the REBORN API.

This module provides a Django management command for data migration.
"""

import os
import time
import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from core.infrastructure.container import Container
from core.application.interfaces.services import PaperService
from core.application.dtos.input_dtos import ScraperUrlInputDTO

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command for data migration."""

    help = "Migrate data from specified sources"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--source",
            type=str,
            choices=["file", "url"],
            default="file",
            help="Source of data: file (JSON file with URLs) or url (single URL)",
        )
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Input file path (for file source) or URL (for url source)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5,
            help="Batch size for processing multiple URLs",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Timeout in seconds between URL processing",
        )
        parser.add_argument(
            "--skip-existing", action="store_true", help="Skip already existing papers"
        )

    def handle(self, *args, **options):
        """Handle command execution."""
        source = options["source"]
        input_value = options["input"]
        batch_size = options["batch_size"]
        timeout = options["timeout"]
        skip_existing = options["skip_existing"]

        try:
            paper_service = Container.get_paper_service()

            if source == "file":
                self.process_file(
                    paper_service, input_value, batch_size, timeout, skip_existing
                )
            elif source == "url":
                self.process_url(paper_service, input_value, skip_existing)
            else:
                raise CommandError(f"Unknown source: {source}")

            self.stdout.write(
                self.style.SUCCESS("Data migration completed successfully")
            )

        except Exception as e:
            logger.error(f"Error during data migration: {str(e)}")
            raise CommandError(f"Error during data migration: {str(e)}")

    def process_file(
        self,
        paper_service: PaperService,
        file_path: str,
        batch_size: int,
        timeout: int,
        skip_existing: bool,
    ):
        """Process a file containing URLs."""
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise CommandError(f"Expected a JSON array of URLs, got: {type(data)}")

            total_urls = len(data)
            self.stdout.write(f"Found {total_urls} URLs to process")

            # Process URLs in batches
            for i in range(0, total_urls, batch_size):
                batch = data[i : i + batch_size]
                self.stdout.write(
                    f"Processing batch {i // batch_size + 1}/{(total_urls + batch_size - 1) // batch_size}"
                )

                for j, url in enumerate(batch):
                    self.stdout.write(
                        f"  Processing URL {i + j + 1}/{total_urls}: {url}"
                    )

                    try:
                        self.process_url(paper_service, url, skip_existing)
                        self.stdout.write(
                            self.style.SUCCESS(f"  Successfully processed URL: {url}")
                        )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  Error processing URL {url}: {str(e)}")
                        )
                        logger.error(f"Error processing URL {url}: {str(e)}")

                # Wait between batches to avoid overloading the server
                if i + batch_size < total_urls:
                    self.stdout.write(f"Waiting {timeout} seconds before next batch...")
                    time.sleep(timeout)

        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {str(e)}")

        except Exception as e:
            raise CommandError(f"Error processing file: {str(e)}")

    def process_url(self, paper_service: PaperService, url: str, skip_existing: bool):
        """Process a single URL."""
        # Check if the paper already exists
        if skip_existing:
            # TODO: Implement check for existing paper
            pass

        url_dto = ScraperUrlInputDTO(url=url)
        result = paper_service.extract_paper(url_dto)

        if not result.success:
            raise CommandError(f"Failed to extract paper from URL: {result.message}")
