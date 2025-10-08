import logging
import time
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Q
from tqdm import tqdm

from core.infrastructure.models.sql_models import (
    Article as ArticleModel,
    Statement as StatementModel,
)
from core.infrastructure.container import Container
from core.application.interfaces.repositories import SearchRepository

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Manage Weaviate indices for articles and statements"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        index_parser = subparsers.add_parser(
            "index", help="Index articles and statements"
        )
        index_parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of items to process in each batch",
        )
        index_parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset the Weaviate indices before indexing",
        )
        index_parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit the number of items to process (0 for all)",
        )
        index_parser.add_argument(
            "--only-articles",
            action="store_true",
            help="Index only articles (skip statements)",
        )
        index_parser.add_argument(
            "--only-statements",
            action="store_true",
            help="Index only statements (skip articles)",
        )
        index_parser.add_argument(
            "--since",
            type=str,
            help="Only index items updated since this date (format: YYYY-MM-DD)",
        )

        delete_parser = subparsers.add_parser(
            "delete", help="Delete items from indices"
        )
        delete_parser.add_argument(
            "--article-id",
            type=str,
            help="Delete a specific article by ID",
        )
        delete_parser.add_argument(
            "--statement-id",
            type=str,
            help="Delete a specific statement by ID",
        )
        delete_parser.add_argument(
            "--reset-all",
            action="store_true",
            help="Reset all indices (delete everything)",
        )

        update_parser = subparsers.add_parser("update", help="Update items in indices")
        update_parser.add_argument(
            "--article-id",
            type=str,
            help="Update a specific article by ID",
        )
        update_parser.add_argument(
            "--statement-id",
            type=str,
            help="Update a specific statement by ID",
        )
        update_parser.add_argument(
            "--since",
            type=str,
            help="Update all items modified since this date (format: YYYY-MM-DD)",
        )
        update_parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of items to process in each batch",
        )

    def handle(self, *args, **options):
        if not settings.USE_WEAVIATE:
            self.stdout.write(
                self.style.ERROR(
                    "Weaviate is not enabled. Set USE_WEAVIATE=true in your environment."
                )
            )
            return

        command = options.get("command", "index")

        try:
            search_repo = Container.resolve(SearchRepository)

            if command == "index":
                self._handle_index(search_repo, options)
            elif command == "delete":
                self._handle_delete(search_repo, options)
            elif command == "update":
                self._handle_update(search_repo, options)
            else:
                self.stdout.write(self.style.ERROR(f"Unknown command: {command}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            logger.error(
                f"Error in Weaviate management command: {str(e)}", exc_info=True
            )

    def _handle_index(self, search_repo, options):
        batch_size = options["batch_size"]
        reset = options["reset"]
        limit = options["limit"]
        only_articles = options["only_articles"]
        only_statements = options["only_statements"]
        since_str = options.get("since")

        since_date = None
        if since_str:
            try:
                since_date = datetime.datetime.strptime(since_str, "%Y-%m-%d").date()
                self.stdout.write(
                    self.style.SUCCESS(f"Indexing items updated since {since_date}")
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Invalid date format. Use YYYY-MM-DD")
                )
                return

        if only_articles and only_statements:
            self.stdout.write(
                self.style.ERROR(
                    "Cannot use both --only-articles and --only-statements at the same time"
                )
            )
            return

        if reset:
            self.stdout.write(self.style.WARNING("Resetting Weaviate indices..."))
            search_repo.delete_indices()
            self.stdout.write(self.style.SUCCESS("Weaviate indices reset successfully"))
        if not only_statements:
            self._process_articles(search_repo, batch_size, limit, since_date)

        if not only_articles:
            self._process_statements(search_repo, batch_size, limit, since_date)

    def _handle_delete(self, search_repo, options):
        article_id = options.get("article_id")
        statement_id = options.get("statement_id")
        reset_all = options.get("reset_all")

        if reset_all:
            self.stdout.write(self.style.WARNING("Resetting all Weaviate indices..."))
            search_repo.delete_indices()
            self.stdout.write(
                self.style.SUCCESS("All Weaviate indices reset successfully")
            )
            return

        if article_id:
            self.stdout.write(
                self.style.WARNING(f"Deleting article from Weaviate: {article_id}")
            )
            result = search_repo.delete_article(article_id)
            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully deleted article: {article_id}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to delete article: {article_id}")
                )

        if statement_id:
            self.stdout.write(
                self.style.WARNING(f"Deleting statement from Weaviate: {statement_id}")
            )
            result = search_repo.delete_statement(statement_id)
            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted statement: {statement_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to delete statement: {statement_id}")
                )

        if not (article_id or statement_id or reset_all):
            self.stdout.write(
                self.style.ERROR(
                    "You must specify --article-id, --statement-id, or --reset-all"
                )
            )

    def _handle_update(self, search_repo, options):
        article_id = options.get("article_id")
        statement_id = options.get("statement_id")
        since_str = options.get("since")
        batch_size = options.get("batch_size", 100)

        since_date = None
        if since_str:
            try:
                since_date = datetime.datetime.strptime(since_str, "%Y-%m-%d").date()
                self.stdout.write(
                    self.style.SUCCESS(f"Updating items modified since {since_date}")
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Invalid date format. Use YYYY-MM-DD")
                )
                return

        if article_id:
            self._update_single_article(search_repo, article_id)

        if statement_id:
            self._update_single_statement(search_repo, statement_id)

        if since_date:
            self._update_articles_since(search_repo, since_date, batch_size)
            self._update_statements_since(search_repo, since_date, batch_size)

        if not (article_id or statement_id or since_date):
            self.stdout.write(
                self.style.ERROR(
                    "You must specify --article-id, --statement-id, or --since"
                )
            )

    def _process_articles(self, search_repo, batch_size, limit, since_date=None):
        queryset = ArticleModel.objects.all().order_by("id")

        if since_date:
            since_datetime = datetime.datetime.combine(since_date, datetime.time.min)
            queryset = queryset.filter(updated_at__gte=since_datetime)

        if limit > 0:
            queryset = queryset[:limit]

        total = queryset.count()
        self.stdout.write(
            self.style.SUCCESS(f"Found {total} articles to index in Weaviate")
        )

        batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

        start_time = time.time()
        indexed_count = 0
        for batch in tqdm(range(batches), desc="Indexing article batches"):
            offset = batch * batch_size
            articles_batch = queryset[offset : offset + batch_size]

            articles_data = []
            for article in articles_batch:
                article_data = {
                    "article_id": article.article_id,
                    "title": article.name,
                    "abstract": article.abstract or "",
                    "updated_at": article.updated_at.isoformat()
                    if article.updated_at
                    else None,
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

    def _statement_data_info(self, data_type):
        long_string = ""
        for data_item in data_type:
            if "has_part" in data_item:
                has_part = data_item["has_part"]

                if "label" in has_part:
                    value = has_part["label"]
                    if value is not None:
                        long_string += str(value) + ", "

                if "executes" in has_part:
                    for execute_item in has_part["executes"]:
                        if "label" in execute_item:
                            value = execute_item["label"]
                            if value is not None:
                                long_string += str(value) + ", "
                        if "part_of" in execute_item:
                            for part_of_item in execute_item["part_of"]:
                                if "label" in part_of_item:
                                    value = part_of_item["label"]
                                    if value is not None:
                                        long_string += str(value) + ", "
                                if (
                                    "part_of" in part_of_item
                                    and isinstance(part_of_item["part_of"], dict)
                                    and "label" in part_of_item["part_of"]
                                ):
                                    value = part_of_item["part_of"]["label"]
                                    if value is not None:
                                        long_string += str(value) + ", "

                if "has_input" in has_part:
                    for input_item in has_part["has_input"]:
                        if "comment" in input_item:
                            value = input_item["comment"]
                            if value is not None:
                                long_string += str(value) + ", "
                        if "label" in input_item:
                            value = input_item["label"]
                            if value is not None:
                                long_string += str(value) + ", "
                        if (
                            "source_table" in input_item
                            and input_item["source_table"] is not None
                        ):
                            if "tab_label" in input_item["source_table"]:
                                value = input_item["source_table"]["tab_label"]
                                if value is not None:
                                    long_string += str(value) + ", "
                        if "has_parts" in input_item:
                            for input_has_part_item in input_item["has_parts"]:
                                if "label" in input_has_part_item:
                                    value = input_has_part_item["label"]
                                    if value is not None:
                                        long_string += str(value) + ", "

                if "has_output" in has_part:
                    for output_item in has_part["has_output"]:
                        if "comment" in output_item:
                            value = output_item["comment"]
                            if value is not None:
                                long_string += str(value) + ", "
                        if "label" in output_item:
                            value = output_item["label"]
                            if value is not None:
                                long_string += str(value) + ", "
                        if (
                            "source_table" in output_item
                            and output_item["source_table"] is not None
                        ):
                            if "tab_label" in output_item["source_table"]:
                                value = output_item["source_table"]["tab_label"]
                                if value is not None:
                                    long_string += str(value) + ", "
                        if "has_parts" in output_item:
                            for output_has_part_item in output_item["has_parts"]:
                                if "label" in output_has_part_item:
                                    value = output_has_part_item["label"]
                                    if value is not None:
                                        long_string += str(value) + ", "

                if "level" in has_part:
                    for level_item in has_part["level"]:
                        if "label" in level_item:
                            value = level_item["label"]
                            if value is not None:
                                long_string += str(value) + ", "

                if "targets" in has_part:
                    for target_item in has_part["targets"]:
                        if "label" in target_item:
                            value = target_item["label"]
                            if value is not None:
                                long_string += str(value) + ", "
        return long_string

    def _process_statements(self, search_repo, batch_size, limit, since_date=None):
        queryset = StatementModel.objects.select_related("article").all().order_by("id")

        from core.infrastructure.container import Container
        from core.application.interfaces.services import PaperService

        paper_service = Container.resolve(PaperService)

        if since_date:
            since_datetime = datetime.datetime.combine(since_date, datetime.time.min)
            queryset = queryset.filter(updated_at__gte=since_datetime)

        if limit > 0:
            queryset = queryset[:limit]

        total = queryset.count()
        self.stdout.write(
            self.style.SUCCESS(f"Found {total} statements to index in Weaviate")
        )

        batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

        start_time = time.time()
        indexed_count = 0

        for batch in tqdm(range(batches), desc="Indexing statement batches"):
            offset = batch * batch_size
            statements_batch = queryset[offset : offset + batch_size]

            statements_data = []
            for statement in statements_batch:
                data_type = paper_service.statement_data_type(statement)
                long_string = self._statement_data_info(data_type)
                statement_data = {
                    "statement_id": statement.statement_id,
                    "label": statement.label,
                    "content": long_string,
                    "updated_at": statement.updated_at.isoformat()
                    if statement.updated_at
                    else None,
                }
                statements_data.append(statement_data)

            if statements_data:
                search_repo.add_statements(statements_data)
                indexed_count += len(statements_data)

            if (batch + 1) % 10 == 0 or batch == batches - 1:
                elapsed = time.time() - start_time
                items_per_sec = indexed_count / elapsed if elapsed > 0 else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Indexed {indexed_count}/{total} statements "
                        f"({items_per_sec:.2f} items/sec)"
                    )
                )

        elapsed = time.time() - start_time
        items_per_sec = indexed_count / elapsed if elapsed > 0 else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully indexed {indexed_count} statements in {elapsed:.2f} seconds "
                f"({items_per_sec:.2f} items/sec)"
            )
        )

    def _update_single_article(self, search_repo, article_id):
        try:
            article = ArticleModel.objects.get(article_id=article_id)

            article_data = {
                "article_id": article.article_id,
                "title": article.name,
                "abstract": article.abstract or "",
                "updated_at": article.updated_at.isoformat()
                if article.updated_at
                else None,
            }

            result = search_repo.update_article(article_data)

            if result:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully updated article: {article_id}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to update article: {article_id}")
                )

        except ArticleModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Article not found: {article_id}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating article: {str(e)}"))

    def _update_single_statement(self, search_repo, statement_id):
        try:
            from core.infrastructure.container import Container
            from core.application.interfaces.services import PaperService

            paper_service = Container.resolve(PaperService)

            statement = StatementModel.objects.select_related("article").get(
                statement_id=statement_id
            )
            data_type = paper_service.statement_data_type(statement)
            long_string = self._statement_data_info(data_type)
            statement_data = {
                "statement_id": statement.statement_id,
                "label": statement.label,
                "content": long_string,
                "updated_at": statement.updated_at.isoformat()
                if statement.updated_at
                else None,
            }

            result = search_repo.update_statement(statement_data)

            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated statement: {statement_id}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to update statement: {statement_id}")
                )

        except StatementModel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Statement not found: {statement_id}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating statement: {str(e)}"))

    def _update_articles_since(self, search_repo, since_date, batch_size):
        since_datetime = datetime.datetime.combine(since_date, datetime.time.min)

        queryset = ArticleModel.objects.filter(updated_at__gte=since_datetime).order_by(
            "id"
        )

        total = queryset.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total} articles to update in Weaviate (modified since {since_date})"
            )
        )

        if total == 0:
            return

        batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

        start_time = time.time()
        updated_count = 0

        for batch in tqdm(range(batches), desc="Updating article batches"):
            offset = batch * batch_size
            articles_batch = queryset[offset : offset + batch_size]

            for article in articles_batch:
                article_data = {
                    "article_id": article.article_id,
                    "title": article.name,
                    "abstract": article.abstract or "",
                    "updated_at": article.updated_at.isoformat()
                    if article.updated_at
                    else None,
                }

                result = search_repo.update_article(article_data)

                if result:
                    updated_count += 1

            if (batch + 1) % 5 == 0 or batch == batches - 1:
                elapsed = time.time() - start_time
                items_per_sec = updated_count / elapsed if elapsed > 0 else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated {updated_count}/{total} articles "
                        f"({items_per_sec:.2f} items/sec)"
                    )
                )

        elapsed = time.time() - start_time
        items_per_sec = updated_count / elapsed if elapsed > 0 else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated_count} articles in {elapsed:.2f} seconds "
                f"({items_per_sec:.2f} items/sec)"
            )
        )

    def _update_statements_since(self, search_repo, since_date, batch_size):
        from core.infrastructure.container import Container
        from core.application.interfaces.services import PaperService

        paper_service = Container.resolve(PaperService)
        since_datetime = datetime.datetime.combine(since_date, datetime.time.min)

        queryset = (
            StatementModel.objects.select_related("article")
            .filter(updated_at__gte=since_datetime)
            .order_by("id")
        )

        total = queryset.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total} statements to update in Weaviate (modified since {since_date})"
            )
        )

        if total == 0:
            return

        batches = (total // batch_size) + (1 if total % batch_size > 0 else 0)

        start_time = time.time()
        updated_count = 0

        for batch in tqdm(range(batches), desc="Updating statement batches"):
            offset = batch * batch_size
            statements_batch = queryset[offset : offset + batch_size]

            for statement in statements_batch:
                data_type = paper_service.statement_data_type(statement)
                long_string = self._statement_data_info(data_type)
                statement_data = {
                    "statement_id": statement.statement_id,
                    "label": statement.label,
                    "content": long_string,
                    "updated_at": statement.updated_at.isoformat()
                    if statement.updated_at
                    else None,
                }

                result = search_repo.update_statement(statement_data)

                if result:
                    updated_count += 1

            if (batch + 1) % 5 == 0 or batch == batches - 1:
                elapsed = time.time() - start_time
                items_per_sec = updated_count / elapsed if elapsed > 0 else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated {updated_count}/{total} statements "
                        f"({items_per_sec:.2f} items/sec)"
                    )
                )

        elapsed = time.time() - start_time
        items_per_sec = updated_count / elapsed if elapsed > 0 else 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully updated {updated_count} statements in {elapsed:.2f} seconds "
                f"({items_per_sec:.2f} items/sec)"
            )
        )
