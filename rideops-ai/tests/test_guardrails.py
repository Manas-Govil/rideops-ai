import unittest
from app.guardrails.sql_validator import validate_sql
from app.guardrails.query_limits import apply_query_limits, execute_governed_query


class TestSQLGuardrails(unittest.TestCase):

    def test_valid_select_queries(self):
        """Ensures approved SELECT queries on RideOps tables pass validation."""
        valid_queries = [
            "SELECT * FROM rideops.fact_trips LIMIT 10;",
            "SELECT pickup_location_id, COUNT(*) FROM fact_trips GROUP BY pickup_location_id;",
            "SELECT * FROM dim_taxi_zones WHERE borough = 'Manhattan';",
            "SELECT * FROM v_hourly_demand;",
            "SELECT * FROM v_zone_performance ORDER BY total_revenue DESC LIMIT 5;",
            "WITH cte AS (SELECT * FROM v_clean_trips) SELECT * FROM cte LIMIT 10;",
        ]
        for query in valid_queries:
            result = validate_sql(query)
            self.assertTrue(result.is_valid, f"Expected valid: {query} -> {result.error}")

    def test_blocked_ddl_and_dml(self):
        """Ensures destructive and modifying operations are blocked."""
        blocked_queries = [
            "DROP TABLE fact_trips;",
            "DELETE FROM fact_trips WHERE trip_id = 1;",
            "UPDATE fact_trips SET fare_amount = 0;",
            "INSERT INTO dim_taxi_zones VALUES (999, 'Test', 'Zone', NULL);",
            "TRUNCATE TABLE fact_trips;",
            "ALTER TABLE fact_trips DROP COLUMN fare_amount;",
            "CREATE TABLE test_table (id INT);",
        ]
        for query in blocked_queries:
            result = validate_sql(query)
            self.assertFalse(result.is_valid, f"Expected blocked: {query}")

    def test_sql_injection_multiple_statements(self):
        """Ensures multiple stacked statements separated by semicolons are rejected."""
        query = "SELECT * FROM fact_trips; DROP TABLE fact_trips;"
        result = validate_sql(query)
        self.assertFalse(result.is_valid)
        self.assertIn("Multiple SQL statements", result.error)

    def test_unapproved_table_access(self):
        """Ensures queries cannot access system catalogs or unapproved schemas."""
        unapproved_queries = [
            "SELECT * FROM pg_catalog.pg_user;",
            "SELECT * FROM information_schema.tables;",
            "SELECT * FROM public.secret_table;",
        ]
        for query in unapproved_queries:
            result = validate_sql(query)
            self.assertFalse(result.is_valid, f"Expected blocked: {query}")
            self.assertIn("Access denied to unapproved table", result.error)

    def test_limit_enforcement(self):
        """Ensures missing LIMIT is appended and excessive LIMIT is clamped."""
        # 1. Missing limit
        query_no_limit = "SELECT * FROM fact_trips"
        limited = apply_query_limits(query_no_limit)
        self.assertIn("LIMIT 100", limited)

        # 2. Normal limit preserved
        query_normal_limit = "SELECT * FROM fact_trips LIMIT 25"
        preserved = apply_query_limits(query_normal_limit)
        self.assertIn("LIMIT 25", preserved)

        # 3. Excessive limit clamped
        query_excessive_limit = "SELECT * FROM fact_trips LIMIT 50000"
        clamped = apply_query_limits(query_excessive_limit)
        self.assertIn("LIMIT 1000", clamped)
        self.assertNotIn("50000", clamped)

    def test_live_governed_query_execution(self):
        """Executes a live query against PostgreSQL through the governed executor."""
        result = execute_governed_query("SELECT borough, zone FROM v_zone_performance LIMIT 3;")
        self.assertTrue(result.success)
        self.assertEqual(result.row_count, 3)
        self.assertGreater(result.latency_ms, 0)
        self.assertIn("borough", result.columns)


if __name__ == "__main__":
    unittest.main()
