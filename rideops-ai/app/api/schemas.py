from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question for RideOps AI", min_length=2)


class QueryResponse(BaseModel):
    question: str
    route: str
    sql: Optional[str] = None
    answer: str
    row_count: int = 0
    latency_ms: float = 0.0
    data: Optional[List[Dict[str, Any]]] = None


class AuditLogItem(BaseModel):
    audit_id: int
    timestamp: datetime
    user_question: str
    agent_route: Optional[str] = None
    generated_sql: Optional[str] = None
    execution_status: Optional[str] = None
    rows_returned: int = 0
    latency_ms: Optional[float] = None
    answer: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    total_trips: int
    environment: str
