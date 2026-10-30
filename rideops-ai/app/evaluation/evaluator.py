import logging
import time
from typing import Any, Dict, List
from app.graph.rideops_graph import rideops_graph
from app.guardrails.query_limits import execute_governed_query
from app.database.connection import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EVALUATION_TEST_CASES = [
    {
        "category": "Mobility Analytics",
        "question": "Which pickup zones generated the highest revenue?",
        "expected_route": "SQL_ANALYST_AGENT",
        "should_succeed": True
    },
    {
        "category": "Mobility Analytics",
        "question": "What are the busiest hours?",
        "expected_route": "SQL_ANALYST_AGENT",
        "should_succeed": True
    },
    {
        "category": "Mobility Analytics",
        "question": "Which zones have the most trips?",
        "expected_route": "SQL_ANALYST_AGENT",
        "should_succeed": True
    },
    {
        "category": "Mobility Analytics",
        "question": "What is the average fare by borough?",
        "expected_route": "SQL_ANALYST_AGENT",
        "should_succeed": True
    },
    {
        "category": "Mobility Analytics",
        "question": "What percentage of trips are airport trips?",
        "expected_route": "SQL_ANALYST_AGENT",
        "should_succeed": True
    },
    {
        "category": "Data Quality",
        "question": "Which trips appear anomalous?",
        "expected_route": "DATA_QUALITY_AGENT",
        "should_succeed": True
    },
    {
        "category": "Data Quality",
        "question": "What are the most common data-quality problems?",
        "expected_route": "DATA_QUALITY_AGENT",
        "should_succeed": True
    },
    {
        "category": "System Help",
        "question": "What tables and views are available in the schema?",
        "expected_route": "HELP_AGENT",
        "should_succeed": True
    },
    {
        "category": "Guardrail Security",
        "sql": "DROP TABLE rideops.fact_trips;",
        "expected_blocked": True
    },
    {
        "category": "Guardrail Security",
        "sql": "DELETE FROM rideops.fact_trips WHERE 1=1;",
        "expected_blocked": True
    },
    {
        "category": "Guardrail Security",
        "sql": "UPDATE rideops.fact_trips SET fare_amount = 0;",
        "expected_blocked": True
    },
    {
        "category": "Guardrail Security",
        "sql": "SELECT 1; DROP TABLE rideops.fact_trips;",
        "expected_blocked": True
    },
    {
        "category": "Guardrail Security",
        "sql": "SELECT * FROM pg_catalog.pg_user;",
        "expected_blocked": True
    },
]


def run_evaluation() -> Dict[str, Any]:
    """Runs the full RideOps governance, latency, and agent accuracy evaluation suite."""
    print("=" * 75)
    print("RIDEOPS AI - SYSTEM BENCHMARK & EVALUATION SUITE")
    print("=" * 75)

    total_tests = len(EVALUATION_TEST_CASES)
    passed_tests = 0
    routing_matches = 0
    routing_tests = 0
    security_blocked = 0
    security_tests = 0
    latencies: List[float] = []

    for idx, tc in enumerate(EVALUATION_TEST_CASES, start=1):
        cat = tc["category"]

        if "question" in tc:
            # Multi-Agent Routing & Query Evaluation
            routing_tests += 1
            q = tc["question"]
            res = rideops_graph.invoke(q)
            latencies.append(res.get("latency_ms", 0.0))

            route_correct = (res.get("route") == tc["expected_route"])
            if route_correct:
                routing_matches += 1

            has_answer = bool(res.get("answer"))
            test_passed = route_correct and has_answer
            if test_passed:
                passed_tests += 1

            status = "PASS" if test_passed else "FAIL"
            print(f"[{status}] Test {idx:02d} | Category: {cat:20} | Route: {res.get('route'):18} | Latency: {res.get('latency_ms', 0):6.1f}ms")

        elif "sql" in tc:
            # SQL Guardrail Security Evaluation
            security_tests += 1
            sql = tc["sql"]
            res = execute_governed_query(sql)

            is_blocked = not res.success
            if is_blocked:
                security_blocked += 1
                passed_tests += 1

            status = "PASS" if is_blocked else "FAIL"
            print(f"[{status}] Test {idx:02d} | Category: {cat:20} | Blocked: {str(is_blocked):5} | Reason: {res.error[:35]}...")

    # Verify Audit Logging
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM rideops.agent_audit_log;")
            audit_count = cur.fetchone()[0]

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    routing_accuracy = (routing_matches / routing_tests * 100) if routing_tests else 100.0
    security_score = (security_blocked / security_tests * 100) if security_tests else 100.0
    overall_score = (passed_tests / total_tests * 100)

    print("\n" + "=" * 75)
    print("EVALUATION SCORECARD")
    print("=" * 75)
    print(f"Overall Tests Passed:       {passed_tests}/{total_tests} ({overall_score:.1f}%)")
    print(f"Agent Routing Accuracy:     {routing_matches}/{routing_tests} ({routing_accuracy:.1f}%)")
    print(f"Guardrail Security Defense: {security_blocked}/{security_tests} ({security_score:.1f}%)")
    print(f"Average Agent Latency:      {avg_latency:.2f} ms (Target SLA: < 3,000 ms)")
    print(f"Verified Audit Log Count:   {audit_count:,} events recorded in PostgreSQL")
    print("=" * 75)

    return {
        "passed": passed_tests,
        "total": total_tests,
        "overall_score": overall_score,
        "routing_accuracy": routing_accuracy,
        "security_score": security_score,
        "avg_latency_ms": avg_latency,
        "audit_count": audit_count
    }


if __name__ == "__main__":
    run_evaluation()
