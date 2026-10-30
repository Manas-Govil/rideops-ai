import logging
import time
from typing import Dict, Any, List
from app.database.queries import record_agent_audit_log
from app.guardrails.query_limits import execute_governed_query

logger = logging.getLogger(__name__)


def generate_quality_sql(question: str) -> str:
    """Generates governed SQL for data quality and anomaly inquiries."""
    q_lower = question.lower()

    if "critical" in q_lower:
        return """
            SELECT issue_type, severity, total_occurrences, distinct_trips_affected, sample_description
            FROM v_quality_issue_summary
            WHERE severity = 'CRITICAL'
            ORDER BY total_occurrences DESC;
        """
    elif "anomal" in q_lower and ("sample" in q_lower or "which" in q_lower or "show" in q_lower):
        return """
            SELECT trip_id, pickup_datetime, dropoff_datetime, trip_duration,
                   fare_amount, trip_distance, fare_per_mile
            FROM fact_trips
            WHERE anomaly_flag = TRUE
            LIMIT 10;
        """
    elif "count" in q_lower or "percentage" in q_lower or "breakdown" in q_lower or "how many" in q_lower:
        return """
            SELECT 
                anomaly_flag,
                COUNT(*) AS total_trips,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
            FROM fact_trips
            GROUP BY anomaly_flag
            ORDER BY anomaly_flag DESC;
        """
    else:
        # Default: overall quality issue summary
        return """
            SELECT issue_type, severity, total_occurrences, distinct_trips_affected, sample_description
            FROM v_quality_issue_summary
            ORDER BY total_occurrences DESC;
        """


def format_quality_answer(rows: List[Dict[str, Any]], question: str) -> str:
    """Formats structured quality findings into executive markdown."""
    if not rows:
        return "No data quality issues matching the criteria were found."

    # If asking for anomaly breakdown (anomaly_flag vs count)
    if "anomaly_flag" in rows[0]:
        total_trips = sum(r["total_trips"] for r in rows)
        anomalies = next((r for r in rows if r["anomaly_flag"] is True), None)
        valid = next((r for r in rows if r["anomaly_flag"] is False), None)

        return f"""### Data Quality & Anomaly Report

* **Total Dataset Rows Analyzed:** {total_trips:,}
* **Valid Operational Trips:** {valid['total_trips']:,} ({valid['percentage']}%)
* **Flagged Anomalies:** {anomalies['total_trips']:,} ({anomalies['percentage']}%)

All anomalous records were retained in `rideops.fact_trips` with `anomaly_flag = TRUE` and mapped to specific root causes in `rideops.data_quality_issues`.
"""

    # If asking for quality issue summary table
    if "issue_type" in rows[0]:
        lines = [
            "### Data Quality Issue Breakdown",
            "",
            "| Issue Type | Severity | Occurrences | Affected Trips | Sample Description |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for r in rows:
            lines.append(
                f"| `{r['issue_type']}` | **{r['severity']}** | {r['total_occurrences']:,} | {r['distinct_trips_affected']:,} | {r.get('sample_description', '')} |"
            )
        return "\n".join(lines)

    # If asking for sample anomalous trips
    if "trip_id" in rows[0]:
        lines = [
            "### Sample Flagged Anomalous Trips",
            "",
            "| Trip ID | Pickup | Duration (min) | Fare ($) | Distance (mi) | Fare/Mile ($) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        for r in rows:
            lines.append(
                f"| {r['trip_id']} | {r['pickup_datetime']} | {r['trip_duration']} | ${r['fare_amount']} | {r['trip_distance']} | {r.get('fare_per_mile', 'N/A')} |"
            )
        return "\n".join(lines)

    return f"Query returned {len(rows)} records."


def handle_quality_query(question: str) -> Dict[str, Any]:
    """
    Executes a governed data quality analysis workflow:
    1. Generates governed SQL.
    2. Runs through SQL Guardrails.
    3. Synthesizes explanation.
    4. Logs to agent_audit_log.
    """
    start_time = time.time()
    sql = generate_quality_sql(question)
    query_result = execute_governed_query(sql)

    if query_result.success:
        answer = format_quality_answer(query_result.rows, question)
        status = "SUCCESS"
    else:
        answer = f"Data quality query failed guardrail verification: {query_result.error}"
        status = "GUARDRAIL_BLOCKED"

    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Record Audit Log
    record_agent_audit_log(
        user_question=question,
        agent_route="DATA_QUALITY_AGENT",
        generated_sql=query_result.sql,
        execution_status=status,
        rows_returned=query_result.row_count,
        latency_ms=latency_ms,
        answer=answer
    )

    return {
        "route": "DATA_QUALITY_AGENT",
        "question": question,
        "sql": query_result.sql,
        "success": query_result.success,
        "row_count": query_result.row_count,
        "latency_ms": latency_ms,
        "answer": answer,
        "data": query_result.rows
    }
