import logging
from pathlib import Path
import pandas as pd
from psycopg2.extras import execute_values
from app.config import BASE_DIR
from app.database.connection import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ZONE_CLEAN_CSV = BASE_DIR / "data" / "processed" / "taxi_zone_lookup_clean.csv"


def load_taxi_zones(csv_path: Path = ZONE_CLEAN_CSV) -> int:
    """Loads clean taxi zones CSV into rideops.dim_taxi_zones table."""
    logger.info("=" * 60)
    logger.info("RIDEOPS AI - LOADING TAXI ZONES")
    logger.info("=" * 60)

    if not csv_path.exists():
        raise FileNotFoundError(f"Clean taxi zone lookup file not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.info("Read %d records from %s", len(df), csv_path)

    expected_cols = {"location_id", "borough", "zone"}
    if not expected_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV columns {df.columns.tolist()} do not match expected {expected_cols}")

    # Prepare tuples for insertion (service_zone remains NULL)
    records = [
        (int(row["location_id"]), str(row["borough"]), str(row["zone"]), None)
        for _, row in df.iterrows()
    ]

    insert_query = """
        INSERT INTO rideops.dim_taxi_zones (location_id, borough, zone, service_zone)
        VALUES %s
        ON CONFLICT (location_id) DO UPDATE SET
            borough = EXCLUDED.borough,
            zone = EXCLUDED.zone,
            service_zone = EXCLUDED.service_zone;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, records, page_size=500)
            cur.execute("SELECT COUNT(*) FROM rideops.dim_taxi_zones;")
            total_loaded = cur.fetchone()[0]

    logger.info("Successfully loaded and verified %d taxi zones in rideops.dim_taxi_zones!", total_loaded)
    logger.info("=" * 60)
    return total_loaded


if __name__ == "__main__":
    load_taxi_zones()
