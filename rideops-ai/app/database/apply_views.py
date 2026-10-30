import logging
from pathlib import Path
from app.config import BASE_DIR
from app.database.connection import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

VIEWS_SQL_PATH = BASE_DIR / "sql" / "views.sql"


def apply_views(sql_path: Path = VIEWS_SQL_PATH):
    """Executes sql/views.sql to create analytical views in rideops schema."""
    logger.info("=" * 60)
    logger.info("RIDEOPS AI - APPLYING ANALYTICAL VIEWS")
    logger.info("=" * 60)

    if not sql_path.exists():
        raise FileNotFoundError(f"Views SQL file not found at: {sql_path}")

    sql = sql_path.read_text(encoding="utf-8")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            logger.info("Executed views definition from %s", sql_path.name)

            # Query created views
            cur.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'rideops'
                ORDER BY table_name;
            """)
            views = [row[0] for row in cur.fetchall()]

    logger.info("Created / Updated %d views in schema 'rideops':", len(views))
    for v in views:
        logger.info("  - rideops.%s", v)
    logger.info("=" * 60)
    return views


if __name__ == "__main__":
    apply_views()
