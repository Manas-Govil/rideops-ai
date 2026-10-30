import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.agents.help_agent import handle_help_query
from app.agents.quality_agent import handle_quality_query
from app.agents.sql_agent import handle_sql_query

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    question: str
    route: Optional[str] = None
    sql: Optional[str] = None
    row_count: int = 0
    latency_ms: float = 0.0
    answer: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


class RideOpsGraph:
    """
    Multi-Agent State Graph Orchestrator for RideOps AI.
    Coordinates routing, guardrail validation, agent execution, and response synthesis.
    """

    @staticmethod
    def classify_intent(question: str) -> str:
        """Determines the appropriate agent route based on the question."""
        q_lower = question.lower().strip()

        # Help & Schema Inquiry
        help_keywords = ["help", "schema", "how do you work", "what can i ask", "documentation", "tables", "views", "guide"]
        if any(k in q_lower for k in help_keywords) and not any(k in q_lower for k in ["revenue", "trip", "busiest", "fare"]):
            return "HELP_AGENT"

        # Data Quality & Anomaly Inquiry
        quality_keywords = ["quality", "anomal", "corrupt", "critical", "issue", "invalid", "severity", "negative", "outlier"]
        if any(k in q_lower for k in quality_keywords):
            return "DATA_QUALITY_AGENT"

        # Default: SQL Analyst for mobility & operational metrics
        return "SQL_ANALYST_AGENT"

    def invoke(self, question: str) -> Dict[str, Any]:
        """
        Executes the agent state graph:
        Input Question -> Router Node -> Specialized Agent Node -> Governed Output
        """
        start_time = time.time()
        logger.info("RideOps Graph received question: %s", question)

        route = self.classify_intent(question)
        logger.info("Graph routing decision: %s", route)

        if route == "HELP_AGENT":
            result = handle_help_query(question)
        elif route == "DATA_QUALITY_AGENT":
            result = handle_quality_query(question)
        else:
            result = handle_sql_query(question)

        total_latency = round((time.time() - start_time) * 1000, 2)
        result["total_graph_latency_ms"] = total_latency

        return result


rideops_graph = RideOpsGraph()
