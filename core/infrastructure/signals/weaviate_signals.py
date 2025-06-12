import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from core.infrastructure.models import ArticleModel
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
        }
        search_repo.add_articles([article_data])
        log_message = "Indexed article in Weaviate" if created else "Updated article in Weaviate"
        logger.info(f"{log_message}: {instance.article_id}")
        
    except Exception as e:
        logger.error(f"Error indexing article in Weaviate: {str(e)}", exc_info=True)

@receiver(post_delete, sender=ArticleModel)
def remove_article_from_weaviate(sender, instance, **kwargs):
    if not settings.USE_WEAVIATE:
        return
    
    logger.warning(
        f"Article deletion from Weaviate not implemented: {instance.article_id}. "
        "Consider implementing a custom delete method in WeaviateSearchEngine."
    )
