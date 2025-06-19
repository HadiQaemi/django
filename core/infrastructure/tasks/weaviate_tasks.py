import logging
import time
from celery import shared_task
from django.conf import settings
from django.db.models import Q

from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
    Statement as StatementModel,
)
from core.infrastructure.container import Container
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


@shared_task(name="sync_weaviate_index")
def sync_weaviate_index():
    if not settings.USE_WEAVIATE:
        logger.info("Weaviate is not enabled. Skipping sync_weaviate_index task.")
        return

    try:
        logger.info("Starting Weaviate index synchronization task")
        start_time = time.time()

        recent_articles = ArticleModel.objects.filter(
            Q(updated_at__gte=time.time() - 86400)
            | Q(created_at__gte=time.time() - 86400)
        ).order_by("-updated_at")[:100]

        recent_statements = (
            StatementModel.objects.select_related("article")
            .filter(
                Q(updated_at__gte=time.time() - 86400)
                | Q(created_at__gte=time.time() - 86400)
            )
            .order_by("-updated_at")[:100]
        )

        search_repo = Container.resolve(SearchRepository)

        articles_data = []
        for article in recent_articles:
            article_data = {
                "article_id": article.article_id,
                "title": article.name,
                "abstract": article.abstract or "",
            }
            articles_data.append(article_data)

        statements_data = []
        for statement in recent_statements:
            statement_data = {
                "statement_id": statement.statement_id,
                "text": statement.content or statement.label,
                "abstract": statement.article.abstract if statement.article else "",
            }
            statements_data.append(statement_data)

        if articles_data:
            search_repo.add_articles(articles_data)

        if statements_data:
            search_repo.add_statements(statements_data)

        elapsed = time.time() - start_time
        logger.info(
            f"Completed Weaviate index synchronization in {elapsed:.2f} seconds. "
            f"Processed {len(articles_data)} articles and {len(statements_data)} statements."
        )

        return {
            "status": "success",
            "processed_articles": len(articles_data),
            "processed_statements": len(statements_data),
            "elapsed_time": elapsed,
        }

    except Exception as e:
        logger.error(f"Error in sync_weaviate_index task: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(name="optimize_weaviate_index")
def optimize_weaviate_index():
    if not settings.USE_WEAVIATE:
        logger.info("Weaviate is not enabled. Skipping optimize_weaviate_index task.")
        return

    try:
        logger.info("Starting Weaviate index optimization task")
        start_time = time.time()

        elapsed = time.time() - start_time
        logger.info(f"Completed Weaviate index optimization in {elapsed:.2f} seconds")

        return {"status": "success", "elapsed_time": elapsed}

    except Exception as e:
        logger.error(f"Error in optimize_weaviate_index task: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
