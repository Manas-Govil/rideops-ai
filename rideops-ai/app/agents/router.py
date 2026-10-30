import logging
from typing import Dict, Any
from app.agents.help_agent import handle_help_query
from app.agents.quality_agent import handle_quality_query
from app.agents.sql_agent import handle_sql_query

logger = logging.getLogger(__name__)


def route_and_execute(question: str) -> Dict[str, Any]:
    """
    Intelligently routes a user's question to the specialized agent:
    - HELP_AGENT: Schema, metric definitions, and system guidance.
    - DATA_QUALITY_AGENT: Anomalies, data hygiene, and quality issue breakdowns.
    - SQL_ANALYST_AGENT: NYC mobility, demand, revenue, airport, and zone analytics.
    """
    q_lower = question.lower().strip()

    # 1. Routing to HELP_AGENT
    help_keywords = [
        "help", "schema", "how do you work", "what can i ask",
        "documentation", "tables", "views", "metadata", "guide"
    ]
    if any(k in q_lower for k in help_keywords) and not any(k in q_lower for k in ["revenue", "trip", "busiest", "fare"]):
        logger.info("Routing query to HELP_AGENT: %s", question)
        return handle_help_query(question)

    # 2. Routing to DATA_QUALITY_AGENT
    quality_keywords = [
        "quality", "anomal", "corrupt", "critical", "issue",
        "invalid", "severity", "negative", "outlier", "hygiene"
    ]
    if any(k in q_lower for k in quality_keywords):
        logger.info("Routing query to DATA_QUALITY_AGENT: %s", question)
        return handle_quality_query(question)

    # 3. Default Routing to SQL_ANALYST_AGENT
    logger.info("Routing query to SQL_ANALYST_AGENT: %s", question)
    return handle_sql_query(question)
