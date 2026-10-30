import re
from typing import List, Optional, Set
from pydantic import BaseModel
from app.config import settings


class SQLValidationResult(BaseModel):
    is_valid: bool
    error: Optional[str] = None
    cleaned_sql: Optional[str] = None
    tables_detected: List[str] = []


# Disallowed DDL and DML keywords
FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCALL\b",
    r"\bCOPY\b",
    r"\bVACUUM\b",
    r"\bCOMMENT\b",
    r"\bREINDEX\b",
    r"\bDISCARD\b",
    r"\bINTO\b",        # e.g. SELECT ... INTO
    r"\bSET\b",         # e.g. SET SESSION AUTHORIZATION
    r"\bPG_SLEEP\b",    # DoS attack prevention
]


def clean_sql(raw_sql: str) -> str:
    """Removes single-line/multi-line comments and normalizes whitespace."""
    # Remove single-line comments (-- ...)
    sql = re.sub(r"--[^\n]*", "", raw_sql)
    # Remove multi-line comments (/* ... */)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Normalize whitespace
    sql = sql.strip()
    return sql


def extract_referenced_tables(sql: str) -> List[str]:
    """
    Extracts table and view names referenced in FROM and JOIN clauses.
    Accounts for CTE (Common Table Expression) alias definitions.
    """
    # Find CTE names defined in WITH cte_name AS (...)
    cte_names: Set[str] = set()
    cte_matches = re.findall(
        r"(?:WITH|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\(",
        sql,
        flags=re.IGNORECASE
    )
    for cte in cte_matches:
        cte_names.add(cte.lower())

    # Match tables following FROM or JOIN
    table_pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)",
        flags=re.IGNORECASE
    )
    matches = table_pattern.findall(sql)

    tables: List[str] = []
    for match in matches:
        clean_name = match.strip().strip('"').strip("'").lower()
        # Exclude subqueries, function calls, or known CTE aliases
        if clean_name not in cte_names and not clean_name.startswith("("):
            tables.append(clean_name)

    return tables


def validate_sql(raw_sql: str) -> SQLValidationResult:
    """
    Validates a SQL query against RideOps governance rules:
    1. Query must be non-empty and well-formed.
    2. Must be SELECT-only (or WITH ... SELECT).
    3. Strictly blocks DDL/DML (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, etc.).
    4. Prohibits multiple stacked statements (semicolon injection).
    5. References ONLY approved tables/views from the RideOps allow-list.
    """
    if not raw_sql or not raw_sql.strip():
        return SQLValidationResult(is_valid=False, error="Empty SQL query provided.")

    cleaned = clean_sql(raw_sql)

    # 1. Prohibit multiple statements (e.g. SELECT 1; DROP TABLE ...)
    statements = [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]
    if len(statements) > 1:
        return SQLValidationResult(
            is_valid=False,
            error="Multiple SQL statements are strictly prohibited.",
            cleaned_sql=cleaned
        )

    # Work with the single statement (strip trailing semicolon if present)
    single_sql = statements[0]

    # 2. Must start with SELECT or WITH
    if not re.match(r"^(SELECT|WITH)\b", single_sql, flags=re.IGNORECASE):
        return SQLValidationResult(
            is_valid=False,
            error="Only read-only SELECT or WITH statements are permitted.",
            cleaned_sql=single_sql
        )

    # 3. Check for forbidden DDL / DML keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, single_sql, flags=re.IGNORECASE):
            keyword = pattern.replace(r"\b", "")
            return SQLValidationResult(
                is_valid=False,
                error=f"Forbidden keyword '{keyword}' detected. Modification operations are blocked.",
                cleaned_sql=single_sql
            )

    # 4. Check table allow-list
    referenced_tables = extract_referenced_tables(single_sql)
    if not referenced_tables:
        # e.g., SELECT 1; or math queries are acceptable
        return SQLValidationResult(is_valid=True, cleaned_sql=single_sql, tables_detected=[])

    unapproved_tables: List[str] = []
    for tbl in referenced_tables:
        # Check either exact match or without schema prefix
        short_name = tbl.split(".")[-1]
        if tbl not in settings.ALLOWED_OBJECTS and short_name not in settings.ALLOWED_OBJECTS:
            unapproved_tables.append(tbl)

    if unapproved_tables:
        return SQLValidationResult(
            is_valid=False,
            error=f"Access denied to unapproved table(s): {', '.join(unapproved_tables)}. Only RideOps tables and views are permitted.",
            cleaned_sql=single_sql,
            tables_detected=referenced_tables
        )

    return SQLValidationResult(
        is_valid=True,
        cleaned_sql=single_sql,
        tables_detected=referenced_tables
    )
