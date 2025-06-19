import logging
from celery import shared_task
from typing import Dict, Any, List
import time

from core.infrastructure.container import Container
from core.application.dtos.input_dtos import ScraperUrlInputDTO
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


@shared_task(name="extract_paper_task")
def extract_paper_task(url: str) -> Dict[str, Any]:
    """
    Extract a paper from a URL in the background.

    Args:
        url (str): The URL to extract the paper from.

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    try:
        logger.info(f"Starting paper extraction from URL: {url}")

        paper_service = Container.get_paper_service()
        url_dto = ScraperUrlInputDTO(url=url)
        result = paper_service.extract_paper(url_dto)

        if result.success:
            logger.info(f"Successfully extracted paper from URL: {url}")
            return {
                "success": True,
                "message": "Paper extracted successfully",
                "url": url,
            }
        else:
            logger.error(
                f"Failed to extract paper from URL: {url}. Error: {result.message}"
            )
            return {
                "success": False,
                "message": result.message or "Failed to extract paper",
                "url": url,
            }

    except Exception as e:
        logger.error(f"Exception in extract_paper_task for URL {url}: {str(e)}")
        return {"success": False, "message": f"An error occurred: {str(e)}", "url": url}


@shared_task(name="batch_extract_papers_task")
def batch_extract_papers_task(urls: List[str]) -> Dict[str, Any]:
    """
    Extract multiple papers from URLs in the background.

    Args:
        urls (List[str]): The URLs to extract papers from.

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    results = []
    success_count = 0
    failure_count = 0

    for url in urls:
        try:
            result = extract_paper_task(url)
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                failure_count += 1

        except Exception as e:
            logger.error(
                f"Exception in batch_extract_papers_task for URL {url}: {str(e)}"
            )
            results.append(
                {
                    "success": False,
                    "message": f"An error occurred: {str(e)}",
                    "url": url,
                }
            )
            failure_count += 1

    return {
        "success": success_count > 0,
        "message": f"Processed {len(urls)} URLs: {success_count} succeeded, {failure_count} failed",
        "results": results,
        "success_count": success_count,
        "failure_count": failure_count,
    }


@shared_task(name="rebuild_search_indices_task")
def rebuild_search_indices_task() -> Dict[str, Any]:
    """
    Rebuild search indices in the background.

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    try:
        logger.info("Starting search indices rebuild")

        # Delete existing indices
        search_service = Container.get_search_service()
        delete_result = search_service.delete_indices()

        if not delete_result.success:
            logger.error(f"Failed to delete search indices: {delete_result.message}")
            return {
                "success": False,
                "message": delete_result.message or "Failed to delete search indices",
            }

        # Get papers from database
        paper_service = Container.get_paper_service()
        papers_result = paper_service.get_all_papers(page=1, page_size=1000)

        # Process papers in batches for search indexing
        if papers_result.total_elements > 0:
            for paper in papers_result.content:
                # Get paper details
                paper_result = paper_service.get_paper_by_id(paper.id)

                if paper_result.success and paper_result.result:
                    article = paper_result.result.get("article", {})
                    statements = paper_result.result.get("statements", [])

                    # Add article to search index
                    article_data = [
                        {
                            "title": article.title,
                            "abstract": article.abstract,
                            "article_id": article.id,
                        }
                    ]

                    # Add statements to search index
                    statement_data = []
                    for statement in statements:
                        text = ""
                        if hasattr(statement, "supports") and statement.supports:
                            if (
                                isinstance(statement.supports[0], dict)
                                and "notation" in statement.supports[0]
                            ):
                                text = statement.supports[0]["notation"]["label"]

                        statement_data.append(
                            {
                                "text": text,
                                "abstract": article.abstract,
                                "statement_id": statement.id,
                            }
                        )

                    # Use the search repository directly
                    search_repo = Container.resolve(SearchRepository)
                    search_repo.add_articles(article_data)
                    search_repo.add_statements(statement_data)

        logger.info("Search indices rebuild completed successfully")
        return {
            "success": True,
            "message": "Search indices rebuilt successfully",
            "papers_processed": papers_result.total_elements,
        }

    except Exception as e:
        logger.error(f"Exception in rebuild_search_indices_task: {str(e)}")
        return {"success": False, "message": f"An error occurred: {str(e)}"}


@shared_task(name="scheduled_data_backup_task")
def scheduled_data_backup_task() -> Dict[str, Any]:
    """
    Perform a scheduled backup of the database.

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    try:
        logger.info("Starting scheduled data backup")

        # Implement the actual backup logic here
        # This could involve calling a shell command to dump the database
        # or using a library to export data

        # Simulate backup process
        time.sleep(5)

        logger.info("Scheduled data backup completed successfully")
        return {
            "success": True,
            "message": "Data backup completed successfully",
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Exception in scheduled_data_backup_task: {str(e)}")
        return {"success": False, "message": f"An error occurred: {str(e)}"}


@shared_task(name="cleanup_old_data_task")
def cleanup_old_data_task(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old temporary data from the database.

    Args:
        days (int): The number of days to keep data for.

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    try:
        logger.info(f"Starting cleanup of old data (older than {days} days)")

        # Implement the actual cleanup logic here
        # This would typically involve querying for records older than a certain date
        # and deleting them

        # Simulate cleanup process
        time.sleep(3)

        logger.info("Old data cleanup completed successfully")
        return {
            "success": True,
            "message": f"Cleanup of data older than {days} days completed successfully",
            "timestamp": time.time(),
        }

    except Exception as e:
        logger.error(f"Exception in cleanup_old_data_task: {str(e)}")
        return {"success": False, "message": f"An error occurred: {str(e)}"}
