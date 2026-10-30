import logging
import time
from typing import Any, Dict, List, Optional
from app.database.connection import get_db_connection

logger = logging.getLogger(__name__)


def record_agent_audit_log(
    user_question: str,
    agent_route: str,
    generated_sql: Optional[str] = None,
    execution_status: str = "SUCCESS",
    rows_returned: int = 0,
    latency_ms: float = 0.0,
    answer: str = ""
) -> int:
    """
    Records an agent execution in rideops.agent_audit_log for security,
    governance, and performance monitoring.
    """
    insert_sql = """
        INSERT INTO rideops.agent_audit_log (
            user_question, agent_route, generated_sql,
            execution_status, rows_returned, latency_ms, answer
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING audit_id;
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        user_question,
                        agent_route,
                        generated_sql,
                        execution_status,
                        rows_returned,
                        latency_ms,
                        answer,
                    )
                )
                audit_id = cur.fetchone()[0]
                return audit_id
    except Exception as exc:
        logger.error("Failed to write to agent_audit_log: %s", exc)
        return -1


def get_recent_audit_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs from rideops.agent_audit_log."""
    query = """
        SELECT audit_id, timestamp, user_question, agent_route,
               generated_sql, execution_status, rows_returned, latency_ms, answer
        FROM rideops.agent_audit_log
        ORDER BY timestamp DESC
        LIMIT %s;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit,))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_rideops_schema_description() -> str:
    """
    Returns a structured textual description of RideOps tables and views
    to guide the agents in query generation and user assistance.
    """
    return """
RideOps Governed Schema:

1. rideops.v_clean_trips (View of valid trips, anomaly_flag = FALSE):
   - trip_id (BIGINT): Unique trip identifier
   - pickup_datetime, dropoff_datetime (TIMESTAMP)
   - pickup_hour (INT, 0-23): Hour of pickup
   - pickup_location_id, dropoff_location_id (INT)
   - pickup_borough, pickup_zone (VARCHAR): Names of pickup location
   - dropoff_borough, dropoff_zone (VARCHAR): Names of dropoff location
   - passenger_count (INT)
   - trip_distance (NUMERIC): Distance in miles
   - fare_amount, tip_amount, total_amount (NUMERIC): Monetary amounts
   - trip_duration (NUMERIC): Duration in minutes
   - fare_per_mile, tip_percentage (NUMERIC): Derived unit economics
   - airport_flag (BOOLEAN): True if trip involves JFK, LGA, or EWR

2. rideops.v_hourly_demand (View of hourly aggregated patterns):
   - pickup_hour (INT, 0-23)
   - total_trips (INT)
   - total_revenue (NUMERIC)
   - avg_fare, avg_distance, avg_duration_minutes (NUMERIC)
   - airport_trips (INT)

3. rideops.v_zone_performance (View of zone-level revenue and demand):
   - pickup_location_id (INT)
   - borough (VARCHAR): Borough name
   - zone (VARCHAR): Taxi zone name
   - total_trips (INT)
   - total_revenue (NUMERIC)
   - avg_fare, avg_fare_per_mile, avg_tip_percentage (NUMERIC)

4. rideops.v_quality_issue_summary (View of data quality issues):
   - issue_type (VARCHAR): e.g. NEGATIVE_FARE, INVALID_PASSENGER_COUNT
   - severity (VARCHAR): CRITICAL, HIGH, MEDIUM, LOW
   - total_occurrences (INT)
   - distinct_trips_affected (INT)
   - sample_description (TEXT)

5. rideops.dim_taxi_zones:
   - location_id (INT, PK), borough (VARCHAR), zone (VARCHAR)

6. rideops.fact_trips:
   - Contains all 3.47M raw trips, including anomalies where anomaly_flag = TRUE.

7. rideops.data_quality_issues:
   - Detailed log of individual quality violations linked by trip_id.
"""
