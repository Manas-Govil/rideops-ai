import logging
import time
from typing import Dict, Any, List
from app.database.queries import record_agent_audit_log
from app.guardrails.query_limits import execute_governed_query

logger = logging.getLogger(__name__)


def generate_mobility_sql(question: str) -> str:
    """Translates natural language mobility questions into governed SQL."""
    q_lower = question.lower()

    # 1. Busiest hours / hourly demand
    if "hour" in q_lower or "busiest" in q_lower or "time of day" in q_lower:
        order_col = "total_revenue DESC" if "revenue" in q_lower else "total_trips DESC"
        return f"""
            SELECT pickup_hour, total_trips, total_revenue, avg_fare, avg_distance, airport_trips
            FROM v_hourly_demand
            ORDER BY {order_col};
        """

    # 2. Average fare or revenue by borough
    elif "borough" in q_lower:
        return """
            SELECT 
                pickup_borough AS borough,
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(SUM(total_amount), 2) AS total_revenue
            FROM v_clean_trips
            WHERE pickup_borough IS NOT NULL
            GROUP BY pickup_borough
            ORDER BY total_revenue DESC;
        """

    # 3. Airport trips analysis
    elif "airport" in q_lower:
        return """
            SELECT 
                airport_flag,
                COUNT(*) AS total_trips,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(SUM(total_amount), 2) AS total_revenue
            FROM fact_trips
            WHERE anomaly_flag = FALSE
            GROUP BY airport_flag
            ORDER BY airport_flag DESC;
        """

    # 4. Top zones by average fare
    elif "average fare" in q_lower or "avg fare" in q_lower or "highest fare" in q_lower:
        return """
            SELECT borough, zone, total_trips, avg_fare, total_revenue
            FROM v_zone_performance
            WHERE total_trips >= 100
            ORDER BY avg_fare DESC
            LIMIT 10;
        """

    # 5. Top zones by trip volume
    elif "most trips" in q_lower or "trip volume" in q_lower or "popular" in q_lower:
        return """
            SELECT borough, zone, total_trips, total_revenue, avg_fare
            FROM v_zone_performance
            ORDER BY total_trips DESC
            LIMIT 10;
        """

    # 6. Highest revenue zones (default)
    else:
        return """
            SELECT borough, zone, total_trips, total_revenue, avg_fare, avg_fare_per_mile
            FROM v_zone_performance
            ORDER BY total_revenue DESC
            LIMIT 10;
        """


def format_sql_answer(rows: List[Dict[str, Any]], question: str) -> str:
    """Formats SQL results into an executive analytical answer."""
    if not rows:
        return "No data found matching your query."

    # Hourly demand formatting
    if "pickup_hour" in rows[0]:
        lines = [
            "### NYC Taxi Hourly Demand & Patterns",
            "",
            "| Hour (24h) | Total Trips | Total Revenue ($) | Avg Fare ($) | Avg Miles | Airport Trips |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        for r in rows:
            hour_str = f"{r['pickup_hour']:02d}:00"
            lines.append(
                f"| **{hour_str}** | {r['total_trips']:,} | ${r['total_revenue']:,} | ${r['avg_fare']} | {r['avg_distance']} mi | {r['airport_trips']:,} |"
            )
        top = rows[0]
        lines.append(f"\n*Peak Activity:* Hour **{top['pickup_hour']:02d}:00** with **{top['total_trips']:,} trips** and **${top['total_revenue']:,}** in revenue.")
        return "\n".join(lines)

    # Borough breakdown
    if "borough" in rows[0] and "zone" not in rows[0]:
        lines = [
            "### NYC Mobility Performance by Borough",
            "",
            "| Borough | Total Trips | Total Revenue ($) | Average Fare ($) |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for r in rows:
            lines.append(
                f"| **{r['borough']}** | {r['total_trips']:,} | ${r['total_revenue']:,} | ${r['avg_fare']} |"
            )
        return "\n".join(lines)

    # Airport analysis
    if "airport_flag" in rows[0]:
        airport = next((r for r in rows if r["airport_flag"] is True), None)
        non_airport = next((r for r in rows if r["airport_flag"] is False), None)

        return f"""### Airport Mobility Analysis (JFK, LGA, EWR)

* **Airport Trips:** {airport['total_trips']:,} trips (**{airport['percentage']}%** of all valid trips)
* **Airport Total Revenue:** ${airport['total_revenue']:,}
* **Airport Average Fare:** ${airport['avg_fare']} (vs. ${non_airport['avg_fare']} for non-airport trips)

Airport trips represent **{airport['percentage']}%** of taxi volume but drive disproportionately higher average fares due to longer transit distances.
"""

    # Zone performance breakdown
    if "zone" in rows[0]:
        lines = [
            "### NYC Taxi Zone Performance",
            "",
            "| Borough | Zone | Total Trips | Revenue ($) | Avg Fare ($) |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for r in rows:
            lines.append(
                f"| {r['borough']} | **{r['zone']}** | {r['total_trips']:,} | ${r['total_revenue']:,} | ${r['avg_fare']} |"
            )
        return "\n".join(lines)

    return f"Returned {len(rows)} analytical rows."


def handle_sql_query(question: str) -> Dict[str, Any]:
    """
    Executes a governed SQL Analyst workflow:
    1. Generates governed SQL query.
    2. Enforces SQL Guardrails.
    3. Formats executive response.
    4. Audits operation in agent_audit_log.
    """
    start_time = time.time()
    sql = generate_mobility_sql(question)
    query_result = execute_governed_query(sql)

    if query_result.success:
        answer = format_sql_answer(query_result.rows, question)
        status = "SUCCESS"
    else:
        answer = f"SQL execution error or guardrail rejection: {query_result.error}"
        status = "FAILED"

    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Record Audit Log
    record_agent_audit_log(
        user_question=question,
        agent_route="SQL_ANALYST_AGENT",
        generated_sql=query_result.sql,
        execution_status=status,
        rows_returned=query_result.row_count,
        latency_ms=latency_ms,
        answer=answer
    )

    return {
        "route": "SQL_ANALYST_AGENT",
        "question": question,
        "sql": query_result.sql,
        "success": query_result.success,
        "row_count": query_result.row_count,
        "latency_ms": latency_ms,
        "answer": answer,
        "data": query_result.rows
    }
