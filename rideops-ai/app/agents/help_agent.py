import logging
import time
from typing import Dict, Any
from app.database.queries import record_agent_audit_log, get_rideops_schema_description

logger = logging.getLogger(__name__)


def handle_help_query(question: str) -> Dict[str, Any]:
    """
    Handles user inquiries regarding RideOps system capabilities,
    governed schema definitions, and available analytical metrics.
    """
    start_time = time.time()
    schema_desc = get_rideops_schema_description()

    answer = f"""### RideOps AI System & Schema Guide

RideOps AI is a governed multi-agent mobility analytics platform powered by PostgreSQL and January 2025 NYC Yellow Taxi data (3.47M trips).

#### What you can ask:
1. **Mobility & Revenue Analytics**:
   - *"Which pickup zones generated the highest revenue?"*
   - *"What are the busiest hours of the day?"*
   - *"What is the average fare by borough?"*
   - *"What percentage of trips are airport trips?"*
   - *"Which zones have the most trips?"*

2. **Data Quality & Governance**:
   - *"What are the most common data-quality problems?"*
   - *"How many anomalies were detected in January 2025?"*
   - *"Show me critical quality issues."*
   - *"Why are certain trips flagged as anomalies?"*

3. **Governed Views Available**:
   - `rideops.v_clean_trips`: Operational trips with anomalies excluded (`anomaly_flag = FALSE`).
   - `rideops.v_hourly_demand`: Pre-aggregated hourly demand (0-23), revenue, and trips.
   - `rideops.v_zone_performance`: Revenue, trip count, and fare-per-mile by taxi zone.
   - `rideops.v_quality_issue_summary`: Severity and frequency breakdown of data anomalies.

All queries are executed with SQL Guardrails (read-only, table allow-list, row limits, and query timeouts).
"""
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Record Audit Log
    record_agent_audit_log(
        user_question=question,
        agent_route="HELP_AGENT",
        generated_sql=None,
        execution_status="SUCCESS",
        rows_returned=0,
        latency_ms=latency_ms,
        answer=answer
    )

    return {
        "route": "HELP_AGENT",
        "question": question,
        "sql": None,
        "answer": answer,
        "latency_ms": latency_ms,
        "data": None
    }
