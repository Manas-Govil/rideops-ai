import logging
import re
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.config import settings
from app.database.connection import get_db_connection
from app.guardrails.sql_validator import validate_sql

logger = logging.getLogger(__name__)


class QueryResult(BaseModel):
    success: bool
    sql: str
    row_count: int = 0
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    latency_ms: float = 0.0
    error: Optional[str] = None


def apply_query_limits(sql: str) -> str:
    """
    Enforces safe row limits:
    - Appends LIMIT default (100) if none is provided.
    - Clamps excessive LIMIT values to max (1000).
    """
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)

    if limit_match:
        requested_limit = int(limit_match.group(1))
        if requested_limit > settings.MAX_ROW_LIMIT:
            # Clamp to max limit
            sql = re.sub(
                r"\bLIMIT\s+\d+\b",
                f"LIMIT {settings.MAX_ROW_LIMIT}",
                sql,
                flags=re.IGNORECASE
            )
            logger.warning("Clamped excessive LIMIT %d to max allowed %d", requested_limit, settings.MAX_ROW_LIMIT)
    else:
        # Append default limit
        sql = f"{sql.rstrip(';')} LIMIT {settings.DEFAULT_ROW_LIMIT}"

    return sql


def execute_governed_query(
    raw_sql: str,
    timeout_ms: int = settings.QUERY_TIMEOUT_MS
) -> QueryResult:
    """
    Executes a SQL query strictly governed by RideOps Guardrails:
    1. Validates read-only permissions and table allow-list.
    2. Applies row limit controls (max 1000).
    3. Enforces execution statement timeout in PostgreSQL.
    4. Measures execution latency.
    """
    start_time = time.time()

    # Step 1: Guardrail Validation
    validation = validate_sql(raw_sql)
    if not validation.is_valid:
        logger.warning("SQL Guardrail Rejection: %s | Query: %s", validation.error, raw_sql)
        return QueryResult(
            success=False,
            sql=raw_sql,
            error=validation.error,
            latency_ms=round((time.time() - start_time) * 1000, 2)
        )

    # Step 2: Apply Limit Clamping
    governed_sql = apply_query_limits(validation.cleaned_sql)

    # Step 3: Execute with Statement Timeout & Schema search_path
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Set schema search path and statement timeout for this specific query
                cur.execute("SET LOCAL search_path TO rideops, public;")
                cur.execute(f"SET LOCAL statement_timeout = {int(timeout_ms)};")

                # Execute governed query
                cur.execute(governed_sql)

                columns = [desc[0] for desc in cur.description] if cur.description else []
                raw_rows = cur.fetchall() if cur.description else []

                # Format rows as clean dictionaries
                rows: List[Dict[str, Any]] = [
                    {col: val for col, val in zip(columns, row)}
                    for row in raw_rows
                ]

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return QueryResult(
                    success=True,
                    sql=governed_sql,
                    row_count=len(rows),
                    columns=columns,
                    rows=rows,
                    latency_ms=elapsed_ms
                )

    except Exception as exc:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        error_msg = str(exc)
        logger.error("Query Execution Error (%s ms): %s", elapsed_ms, error_msg)
        return QueryResult(
            success=False,
            sql=governed_sql,
            error=f"Database execution error: {error_msg}",
            latency_ms=elapsed_ms
        )
