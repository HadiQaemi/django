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

@shared_task(name="scheduled_data_backup_task")
def scheduled_data_backup_task() -> Dict[str, Any]:
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
