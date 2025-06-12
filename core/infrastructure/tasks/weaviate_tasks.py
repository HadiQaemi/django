import logging
import time
from celery import shared_task
from django.conf import settings
from django.db.models import Q

from core.infrastructure.models import ArticleModel
from core.infrastructure.container import Container
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


@shared_task(name="sync_weaviate_index")
def sync_weaviate_index():
    """
    Synchronize Weaviate index with the database.

    This task checks for articles that might have been missed in the Weaviate index
    due to failures or race conditions and ensures they are properly indexed.
    """
    if not settings.USE_WEAVIATE:
        logger.info("Weaviate is not enabled. Skipping sync_weaviate_index task.")
        return

    try:
        logger.info("Starting Weaviate index synchronization task")
        start_time = time.time()

        # Get the most recent articles (last 24 hours)
        recent_articles = ArticleModel.objects.filter(
            Q(updated_at__gte=time.time() - 86400)
            | Q(created_at__gte=time.time() - 86400)
        ).order_by("-updated_at")[:100]

        # Get the search repository
        search_repo = Container.resolve(SearchRepository)

        # Prepare articles for indexing
        articles_data = []
        for article in recent_articles:
            article_data = {
                "article_id": article.article_id,
                "title": article.name,
                "abstract": article.abstract or "",
            }
            articles_data.append(article_data)

        # Index the articles
        if articles_data:
            search_repo.add_articles(articles_data)

        elapsed = time.time() - start_time
        logger.info(
            f"Completed Weaviate index synchronization in {elapsed:.2f} seconds. "
            f"Processed {len(articles_data)} articles."
        )

        return {
            "status": "success",
            "processed_count": len(articles_data),
            "elapsed_time": elapsed,
        }

    except Exception as e:
        logger.error(f"Error in sync_weaviate_index task: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="optimize_weaviate_index")
def optimize_weaviate_index():
    """
    Perform periodic optimization of the Weaviate index.

    Currently, Weaviate handles most optimization automatically. This task is
    a placeholder for future optimizations that might be needed.
    """
    if not settings.USE_WEAVIATE:
        logger.info("Weaviate is not enabled. Skipping optimize_weaviate_index task.")
        return

    try:
        logger.info("Starting Weaviate index optimization task")
        start_time = time.time()

        # Note: Weaviate handles most optimization automatically
        # This is a placeholder for future optimizations if needed

        elapsed = time.time() - start_time
        logger.info(f"Completed Weaviate index optimization in {elapsed:.2f} seconds")

        return {"status": "success", "elapsed_time": elapsed}

    except Exception as e:
        logger.error(f"Error in optimize_weaviate_index task: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
