import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.api.schemas import QueryRequest, QueryResponse, AuditLogItem, HealthResponse
from app.config import settings
from app.database.connection import get_db_connection
from app.database.queries import get_recent_audit_logs, get_rideops_schema_description
from app.graph.rideops_graph import rideops_graph

logger = logging.getLogger(__name__)
api_router = APIRouter()


@api_router.post("/query", response_model=QueryResponse, summary="Query RideOps Multi-Agent System")
def process_user_query(payload: QueryRequest):
    """
    Submits a natural language mobility or data quality inquiry to the
    governed multi-agent system.
    """
    try:
        result = rideops_graph.invoke(payload.question)
        return QueryResponse(
            question=payload.question,
            route=result.get("route", "UNKNOWN"),
            sql=result.get("sql"),
            answer=result.get("answer", "No response generated."),
            row_count=result.get("row_count", 0),
            latency_ms=result.get("latency_ms", 0.0),
            data=result.get("data")
        )
    except Exception as exc:
        logger.error("Error processing query '%s': %s", payload.question, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/audit-logs", response_model=List[AuditLogItem], summary="Get Agent Audit Trail")
def get_audit_trail(limit: int = Query(20, ge=1, le=100)):
    """Retrieves recent audit logs from rideops.agent_audit_log for compliance and auditing."""
    try:
        logs = get_recent_audit_logs(limit=limit)
        return logs
    except Exception as exc:
        logger.error("Error fetching audit logs: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/schema", summary="Get Governed Schema Documentation")
def get_schema():
    """Returns the RideOps approved schema structure and descriptions."""
    return {"schema": get_rideops_schema_description()}


@api_router.get("/health", response_model=HealthResponse, summary="System Health & Readiness")
def health_check():
    """Checks database connectivity and records count in fact_trips."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM rideops.fact_trips;")
                total_trips = cur.fetchone()[0]

        return HealthResponse(
            status="healthy",
            database_connected=True,
            total_trips=total_trips,
            environment=settings.ENVIRONMENT
        )
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            total_trips=0,
            environment=settings.ENVIRONMENT
        )
