import io
import logging
from pathlib import Path
from typing import List, Tuple
import pandas as pd
from psycopg2.extras import execute_values
from app.config import BASE_DIR
from app.database.connection import get_db_connection

logger = logging.getLogger(__name__)

INDEXES_SQL_PATH = BASE_DIR / "sql" / "indexes.sql"


def get_current_max_trip_id() -> int:
    """Returns the current maximum trip_id from fact_trips (0 if empty)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(trip_id), 0) FROM rideops.fact_trips;")
            return cur.fetchone()[0]


def load_trip_batch_copy(cur, df: pd.DataFrame) -> int:
    """
    Loads a batch of transformed trips into rideops.fact_trips using high-speed PostgreSQL COPY.
    """
    buffer = io.StringIO()
    # Write TSV without headers, using \N for NULL
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N")
    buffer.seek(0)

    copy_sql = """
        COPY rideops.fact_trips (
            trip_id,
            pickup_datetime,
            dropoff_datetime,
            pickup_location_id,
            dropoff_location_id,
            passenger_count,
            trip_distance,
            fare_amount,
            tip_amount,
            total_amount,
            trip_duration,
            fare_per_mile,
            tip_percentage,
            airport_flag,
            anomaly_flag
        ) FROM STDIN WITH (FORMAT text, NULL '\\N')
    """
    cur.copy_expert(copy_sql, buffer)
    return len(df)


def load_quality_issues_batch(cur, issues: List[Tuple[int, str, str, str]]) -> int:
    """
    Batch inserts data quality issues into rideops.data_quality_issues.
    """
    if not issues:
        return 0

    insert_sql = """
        INSERT INTO rideops.data_quality_issues (trip_id, issue_type, severity, description)
        VALUES %s
    """
    execute_values(cur, insert_sql, issues, page_size=2000)
    return len(issues)


def sync_database_sequences() -> None:
    """Synchronizes PostgreSQL SERIAL sequences with current max IDs."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT setval(
                    'rideops.fact_trips_trip_id_seq',
                    (SELECT COALESCE(MAX(trip_id), 1) FROM rideops.fact_trips)
                );
                SELECT setval(
                    'rideops.data_quality_issues_issue_id_seq',
                    (SELECT COALESCE(MAX(issue_id), 1) FROM rideops.data_quality_issues)
                );
            """)
    logger.info("Synchronized PostgreSQL sequence IDs for fact_trips and data_quality_issues.")


def apply_database_indexes(sql_path: Path = INDEXES_SQL_PATH) -> None:
    """Executes sql/indexes.sql to create analytical indexes."""
    if not sql_path.exists():
        logger.warning("Indexes SQL file not found at: %s", sql_path)
        return

    sql = sql_path.read_text(encoding="utf-8")
    logger.info("Applying database performance indexes from %s...", sql_path.name)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
    logger.info("Database performance indexes created successfully.")
