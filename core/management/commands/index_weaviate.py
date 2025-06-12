import logging
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from tqdm import tqdm

from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
)
from core.infrastructure.container import Container
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Index existing articles in Weaviate for semantic search"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of articles to process in each batch",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset the Weaviate indices before indexing",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit the number of articles to process (0 for all)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        reset = options["reset"]
        limit = options["limit"]

        try:
            search_repo = Container.resolve(SearchRepository)

            if reset:
                self.stdout.write(self.style.WARNING("Resetting Weaviate indices..."))
                search_repo.delete_indices()
                self.stdout.write(
                    self.style.SUCCESS("Weaviate indices reset successfully")
                )

            queryset = ArticleModel.objects.all().order_by("id")
            if limit > 0:
                queryset = queryset.filter(id__lte=limit)

            total = queryset.count()
            self.stdout.write(
                self.style.SUCCESS(f"Found {total} articles to index in Weaviate")
            )

            batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

            start_time = time.time()
            indexed_count = 0

            for batch in tqdm(range(batches), desc="Indexing batches"):
                offset = batch * batch_size
                articles_batch = queryset[offset : offset + batch_size]

                articles_data = []
                for article in articles_batch:
                    article_data = {
                        "article_id": article.article_id,
                        "title": article.name,
                        "abstract": article.abstract or "",
                    }
                    articles_data.append(article_data)

                if articles_data:
                    search_repo.add_articles(articles_data)
                    indexed_count += len(articles_data)

                if (batch + 1) % 10 == 0 or batch == batches - 1:
                    elapsed = time.time() - start_time
                    items_per_sec = indexed_count / elapsed if elapsed > 0 else 0
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Indexed {indexed_count}/{total} articles "
                            f"({items_per_sec:.2f} items/sec)"
                        )
                    )

            elapsed = time.time() - start_time
            items_per_sec = indexed_count / elapsed if elapsed > 0 else 0

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully indexed {indexed_count} articles in {elapsed:.2f} seconds "
                    f"({items_per_sec:.2f} items/sec)"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error indexing articles: {str(e)}"))
            logger.error(f"Error indexing articles: {str(e)}", exc_info=True)
