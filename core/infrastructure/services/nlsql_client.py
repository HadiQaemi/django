import os
import re
import time
import requests
import logging
import duckdb
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from django.conf import settings

from core.infrastructure.models.sql_models import DataItem
from core.infrastructure.utils.id_encoder import decode_paper_id

logger = logging.getLogger(__name__)


@dataclass
class SQLGenerationResult:
    """Result of SQL generation request"""

    success: bool
    sql: Optional[str] = None
    question: str = ""
    confidence: float = 0.0
    similar_examples: list = None
    error: Optional[str] = None


@dataclass
class SQLExecutionResult:
    """Result of SQL execution on data"""

    success: bool
    data: Optional[List[Dict]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    sql: Optional[str] = None
    question: str = ""
    error: Optional[str] = None


class NLSQLClientService:
    """Client service for communicating with NL-SQL Docker service"""

    def __init__(self):
        # Get NL-SQL service URL from settings or use default
        self.base_url = getattr(
            settings, "NLSQL_SERVICE_URL", "https://50bef0a367c8.ngrok-free.app/"
        )
        self.timeout = getattr(settings, "NLSQL_TIMEOUT", 120)

        self.db_path = getattr(
            settings, "DUCKDB_DATABASE_PATH", "data/nlsql_database.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        print(os.path.dirname(self.db_path))

        self.db_conn = None

    def health_check(self) -> Dict[str, Any]:
        """Check if NL-SQL service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"NL-SQL health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get NL-SQL service status: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _get_db_connection(self):
        """Get or create DuckDB connection"""
        if self.db_conn is None:
            self.db_conn = duckdb.connect(":memory:")
            # self.db_conn = duckdb.connect(self.db_path)
            self.db_conn.execute("SET memory_limit='2GB'")
            self.db_conn.execute("SET threads=4")
        return self.db_conn

    def generate_sql(
        self,
        question: str,
        schema: Optional[str] = None,
    ) -> SQLGenerationResult:
        try:
            payload = {"question": question.strip()}

            if schema:
                payload["schema"] = schema
            print(schema)
            response = requests.post(
                f"{self.base_url}/generate_sql",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )
            print(response.text)
            response.raise_for_status()
            result_data = response.json()
            return SQLGenerationResult(
                success=result_data.get("success", False),
                sql=result_data.get("generated_sql"),
                question=result_data.get("question", question),
                confidence=result_data.get("confidence", 0.0),
                similar_examples=result_data.get("similar_examples", []),
                error=result_data.get("error"),
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate SQL: {str(e)}")
            return SQLGenerationResult(
                success=False,
                question=question,
                error=f"Service communication error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Unexpected error in SQL generation: {str(e)}")
            return SQLGenerationResult(
                success=False, question=question, error=f"Unexpected error: {str(e)}"
            )

    def _get_file_path(self, source_file):
        """Get actual file path from Django file field"""
        try:
            if hasattr(source_file, "path"):
                return source_file.path
            elif hasattr(source_file, "url"):
                file_content = source_file.read()
                temp_path = f"/tmp/{source_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                return temp_path
            else:
                return str(source_file)
        except Exception as e:
            logger.error(f"Error getting file path: {str(e)}")
            return None

    def _clean_column_name(self, column_name: str) -> str:
        """Clean column names to be SQL-friendly"""
        import re

        clean_name = str(column_name).strip()
        clean_name = re.sub(r"[^\w]", "_", clean_name)
        clean_name = re.sub(r"_+", "_", clean_name)
        clean_name = clean_name.strip("_")
        clean_name = clean_name.lower()
        if clean_name and not clean_name[0].isalpha() and clean_name[0] != "_":
            clean_name = "col_" + clean_name

        if not clean_name:
            clean_name = ""

        reserved_words = {
            "select",
            "from",
            "where",
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
            "table",
            "index",
            "view",
            "database",
            "schema",
            "order",
            "group",
            "having",
            "join",
            "union",
            "intersect",
            "except",
            "case",
            "when",
            "then",
            "else",
            "end",
            "as",
            "distinct",
            "all",
            "and",
            "or",
            "not",
            "in",
            "like",
            "between",
            "null",
            "true",
            "false",
        }

        if clean_name.lower() in reserved_words:
            clean_name = f"{clean_name}_col"

        return clean_name

    def _clean_data_value(self, value):
        """Clean individual data values"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        if isinstance(value, str):
            value = value.strip()
            null_values = {
                "null",
                "none",
                "n/a",
                "na",
                "nil",
                "?",
                "",
                "undefined",
                "#n/a",
                "#null!",
            }
            if value.lower() in null_values:
                return None
            value = value.replace("\ufeff", "").replace("\x00", "")
            value = value.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')

        return value

    def _load_csv_to_duckdb(self, file_path: str, table_name: str) -> bool:
        # try:
        import pandas as pd

        logger.info(f"Loading and cleaning CSV: {file_path}")
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding="latin-1")
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding="cp1252")

        original_columns = df.columns.tolist()
        cleaned_columns = [self._clean_column_name(col) for col in original_columns]

        seen_columns = {}
        final_columns = []
        for col in cleaned_columns:
            if col in seen_columns:
                seen_columns[col] += 1
                final_columns.append(f"{col}_{seen_columns[col]}")
            else:
                seen_columns[col] = 0
                final_columns.append(col)

        df.columns = final_columns

        for col in df.columns:
            df[col] = df[col].apply(self._clean_data_value)

        for col in df.columns:
            if df[col].dtype == "object":
                numeric_series = pd.to_numeric(df[col], errors="ignore")
                if not numeric_series.equals(df[col]):
                    non_null_count = df[col].count()
                    if non_null_count > 0:
                        numeric_count = pd.to_numeric(df[col], errors="coerce").count()
                        if numeric_count / non_null_count > 0.8:  # 80% numeric
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                            logger.info(f"Converted column '{col}' to numeric")

        initial_shape = df.shape
        df = df.dropna(how="all")
        df = df.loc[:, df.notna().any()]

        if df.shape != initial_shape:
            logger.info(f"Removed empty rows/columns. New shape: {df.shape}")

        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as temp_file:
            df.to_csv(temp_file.name, index=False)
            temp_csv_path = temp_file.name

        conn = self._get_db_connection()

        sql = f"""
        CREATE OR REPLACE TABLE {table_name} AS 
        SELECT * FROM read_csv_auto('{temp_csv_path}', 
            header=true,
            ignore_errors=true,
            null_padding=true
        )
        """

        conn.execute(sql)
        logger.info(f"Successfully loaded CSV {file_path} into table {table_name}")
        return True

        # except Exception as e:
        #     logger.error(f"Error loading CSV to DuckDB: {str(e)}")
        #     return False

    def _get_table_schema(self, table_name: str) -> Optional[str]:
        try:
            conn = self._get_db_connection()

            result = conn.execute(f"DESCRIBE {table_name}").fetchall()

            if not result:
                return None

            # Build CREATE TABLE statement
            columns = []
            for row in result:
                column_name = row[0]
                column_type = row[1]
                columns.append(f"{column_name} {column_type}")

            schema = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);"
            columns_match = re.search(r"\((.*)\)", schema, re.DOTALL)
            columns_text = columns_match.group(1)
            column_lines = [
                line.strip().rstrip(",")
                for line in columns_text.split("\n")
                if line.strip()
            ]
            if len(column_lines):
                selected_columns = []
                table_match = re.search(r"CREATE TABLE (\w+)", schema)
                table_name = table_match.group(1) if table_match else "data_table"
                for col in column_lines[:100]:
                    selected_columns.append(col)
                truncated_schema = (
                    f"CREATE TABLE {table_name} (\n  "
                    + ",\n  ".join(selected_columns)
                    + "\n);"
                )
                return truncated_schema
            logger.debug(f"Generated schema: {schema}")
            return schema

        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            return None

    def _execute_sql_on_data(self, sql: str):
        """Execute SQL query on loaded data"""
        # try:
        conn = self._get_db_connection()
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]

        data = []
        for row in result:
            data.append(dict(zip(columns, row)))
        return SQLExecutionResult(
            success=True, data=data, columns=columns, row_count=len(data), sql=sql
        )

        # except Exception as e:
        #     logger.error(f"Error executing SQL: {str(e)}")
        #     return SQLExecutionResult(
        #         success=False, error=f"SQL execution error: {str(e)}", sql=sql
        #     )

    def generate_and_execute_sql(
        self, question: str, data_item_id: str, table_name: str
    ) -> SQLExecutionResult:
        # try:
        data_item_id = decode_paper_id(data_item_id)
        data_item = DataItem.objects.filter(id=data_item_id).first()
        if not data_item:
            return SQLExecutionResult(
                success=False,
                question=question,
                error="No data items found in database",
                row_count=0,
            )

        # Check if data_item has source_file
        if not hasattr(data_item, "source_file") or not data_item.source_file:
            return SQLExecutionResult(
                success=False,
                question=question,
                error="Data item has no source file",
            )
        # Get file path
        file_path = self._get_file_path(data_item.source_file)
        if not file_path:
            return SQLExecutionResult(
                success=False,
                question=question,
                error="Could not access source file",
            )
        # Check if file exists and is CSV
        if not os.path.exists(file_path):
            return SQLExecutionResult(
                success=False,
                question=question,
                error=f"File not found: {file_path}",
            )

        if not file_path.lower().endswith(".csv"):
            return SQLExecutionResult(
                success=False,
                question=question,
                error="Source file must be a CSV file",
            )

        # Load CSV into DuckDB
        if not self._load_csv_to_duckdb(file_path, table_name):
            return SQLExecutionResult(
                success=False, question=question, error="Failed to load CSV data"
            )

        # Get table schema for better SQL generation
        schema = self._get_table_schema(table_name)

        # Generate SQL using the NL-SQL service
        if len(question.strip()) == 0:
            generation_result = SQLGenerationResult(
                success=True,
                sql=f"SELECT * FROM {table_name};",
                question="",
                error=None,
            )
        else:
            generation_result = self.generate_sql(question, schema)

        if not generation_result.success:
            return SQLExecutionResult(
                success=False, question=question, error=generation_result.error
            )

        # Replace generic table names with our actual table name
        sql = generation_result.sql
        if sql:
            # Replace common table placeholders with our table name
            replacements = [
                "table_name",
                "your_table",
                "data",
                "users",
                "products",
                "sales",
            ]
            for placeholder in replacements:
                sql = sql.replace(placeholder, table_name)

        # Execute SQL on the loaded data
        execution_result = self._execute_sql_on_data(sql)
        execution_result.question = question
        execution_result.confidence = generation_result.confidence

        return execution_result

        # except Exception as e:
        #     logger.error(f"Error in generate_and_execute_sql: {str(e)}")
        #     return SQLExecutionResult(
        #         success=False, question=question, error=f"Unexpected error: {str(e)}"
        #     )

    def close_connection(self):
        """Close DuckDB connection"""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
