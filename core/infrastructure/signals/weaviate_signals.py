import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
    Statement as StatementModel,
)
from core.infrastructure.container import Container
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ArticleModel)
def index_article_in_weaviate(sender, instance, created, **kwargs):
    if not settings.USE_WEAVIATE:
        return

    try:
        search_repo = Container.resolve(SearchRepository)

        article_data = {
            "article_id": instance.article_id,
            "title": instance.name,
            "abstract": instance.abstract or "",
            "updated_at": instance.updated_at.isoformat()
            if instance.updated_at
            else None,
        }

        if created:
            search_repo.add_articles([article_data])
            logger.info(f"Indexed new article in Weaviate: {instance.article_id}")
        else:
            result = search_repo.update_article(article_data)
            if result:
                logger.info(f"Updated article in Weaviate: {instance.article_id}")
            else:
                logger.warning(
                    f"Failed to update article in Weaviate: {instance.article_id}"
                )
                search_repo.add_articles([article_data])
                logger.info(
                    f"Re-indexed article in Weaviate after update failure: {instance.article_id}"
                )

    except Exception as e:
        logger.error(f"Error indexing article in Weaviate: {str(e)}", exc_info=True)


@receiver(post_save, sender=StatementModel)
def index_statement_in_weaviate(sender, instance, created, **kwargs):
    if not settings.USE_WEAVIATE:
        return

    try:
        search_repo = Container.resolve(SearchRepository)
        abstract = ""
        if (
            hasattr(instance, "article")
            and instance.article
            and hasattr(instance.article, "abstract")
        ):
            abstract = instance.article.abstract or ""

        statement_data = {
            "statement_id": instance.statement_id,
            "text": instance.content or instance.label,
            "abstract": abstract,
            "updated_at": instance.updated_at.isoformat()
            if instance.updated_at
            else None,
        }

        if created:
            search_repo.add_statements([statement_data])
            logger.info(f"Indexed new statement in Weaviate: {instance.statement_id}")
        else:
            result = search_repo.update_statement(statement_data)
            if result:
                logger.info(f"Updated statement in Weaviate: {instance.statement_id}")
            else:
                logger.warning(
                    f"Failed to update statement in Weaviate: {instance.statement_id}"
                )
                search_repo.add_statements([statement_data])
                logger.info(
                    f"Re-indexed statement in Weaviate after update failure: {instance.statement_id}"
                )

    except Exception as e:
        logger.error(f"Error indexing statement in Weaviate: {str(e)}", exc_info=True)


@receiver(post_delete, sender=ArticleModel)
def remove_article_from_weaviate(sender, instance, **kwargs):
    if not settings.USE_WEAVIATE:
        return

    try:
        search_repo = Container.resolve(SearchRepository)
        result = search_repo.delete_article(instance.article_id)

        if result:
            logger.info(f"Deleted article from Weaviate: {instance.article_id}")
        else:
            logger.warning(
                f"Failed to delete article from Weaviate: {instance.article_id}"
            )

    except Exception as e:
        logger.error(f"Error deleting article from Weaviate: {str(e)}", exc_info=True)


@receiver(post_delete, sender=StatementModel)
def remove_statement_from_weaviate(sender, instance, **kwargs):
    if not settings.USE_WEAVIATE:
        return

    try:
        search_repo = Container.resolve(SearchRepository)

        result = search_repo.delete_statement(instance.statement_id)

        if result:
            logger.info(f"Deleted statement from Weaviate: {instance.statement_id}")
        else:
            logger.warning(
                f"Failed to delete statement from Weaviate: {instance.statement_id}"
            )

    except Exception as e:
        logger.error(f"Error deleting statement from Weaviate: {str(e)}", exc_info=True)
