import logging
import time
from pathlib import Path
import pyarrow.parquet as pq
from app.config import BASE_DIR, settings
from app.database.connection import get_db_connection
from app.etl.load_zones import load_taxi_zones
from app.etl.transform_trips import transform_trip_batch
from app.etl.load_trips import (
    get_current_max_trip_id,
    load_trip_batch_copy,
    load_quality_issues_batch,
    sync_database_sequences,
    apply_database_indexes,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("RideOps_ETL")

RAW_PARQUET_PATH = BASE_DIR / "data" / "raw" / "yellow_tripdata_2025-01.parquet"


def get_zone_metadata():
    """Fetches valid zone IDs and airport zone IDs from rideops.dim_taxi_zones."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT location_id, borough, zone FROM rideops.dim_taxi_zones;")
            rows = cur.fetchall()

    if not rows:
        logger.info("dim_taxi_zones is empty. Triggering zone loading...")
        load_taxi_zones()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT location_id, borough, zone FROM rideops.dim_taxi_zones;")
                rows = cur.fetchall()

    valid_zone_ids = set(r[0] for r in rows)
    airport_zone_ids = set(
        r[0] for r in rows
        if "airport" in r[2].lower() or "jfk" in r[2].lower() or "laguardia" in r[2].lower() or r[1] == "EWR"
    )
    logger.info("Loaded zone metadata: %d valid zones, %d airport zones (%s)",
                len(valid_zone_ids), len(airport_zone_ids), sorted(airport_zone_ids))
    return valid_zone_ids, airport_zone_ids


def run_etl_pipeline(
    parquet_path: Path = RAW_PARQUET_PATH,
    chunk_size: int = settings.CHUNK_SIZE,
    max_records: int = None,
    create_indexes: bool = True
):
    """
    Executes the RideOps production ETL pipeline in streaming chunks.
    """
    start_total_time = time.time()
    logger.info("=" * 70)
    logger.info("RIDEOPS AI - PRODUCTION ETL PIPELINE")
    logger.info("=" * 70)
    logger.info("Source Parquet: %s", parquet_path)
    logger.info("Chunk Size: %s records", f"{chunk_size:,}")

    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet source file not found: {parquet_path}")

    # 1. Fetch Zone Metadata
    valid_zone_ids, airport_zone_ids = get_zone_metadata()

    # 2. Inspect Parquet
    parquet_file = pq.ParquetFile(str(parquet_path))
    total_parquet_rows = parquet_file.metadata.num_rows
    target_rows = min(total_parquet_rows, max_records) if max_records else total_parquet_rows
    logger.info("Total rows to process: %s", f"{target_rows:,}")

    # 3. Determine Starting trip_id
    current_trip_id = get_current_max_trip_id() + 1
    logger.info("Starting trip_id: %s", f"{current_trip_id:,}")

    # 4. Process Chunks
    total_read = 0
    total_loaded = 0
    total_anomalies = 0
    total_issues = 0
    chunk_index = 0

    batch_iter = parquet_file.iter_batches(batch_size=chunk_size)

    for batch in batch_iter:
        chunk_start = time.time()
        chunk_index += 1

        raw_df = batch.to_pandas()
        if max_records and (total_read + len(raw_df) > max_records):
            raw_df = raw_df.iloc[: (max_records - total_read)]

        batch_len = len(raw_df)
        total_read += batch_len

        # Transform & Quality Checks
        df, issues = transform_trip_batch(
            raw_df=raw_df,
            start_trip_id=current_trip_id,
            valid_zone_ids=valid_zone_ids,
            airport_zone_ids=airport_zone_ids,
        )

        anomalies_in_batch = int(df["anomaly_flag"].sum())
        total_anomalies += anomalies_in_batch
        total_issues += len(issues)

        # Bulk Load to PostgreSQL
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                load_trip_batch_copy(cur, df)
                load_quality_issues_batch(cur, issues)

        total_loaded += batch_len
        current_trip_id += batch_len

        chunk_elapsed = time.time() - chunk_start
        rate = batch_len / chunk_elapsed if chunk_elapsed > 0 else 0
        progress_pct = (total_loaded / target_rows) * 100

        logger.info(
            "Chunk %d | Loaded: %s / %s (%.1f%%) | Anomalies: %d | Issues: %d | Speed: %.0f rows/s",
            chunk_index,
            f"{total_loaded:,}",
            f"{target_rows:,}",
            progress_pct,
            anomalies_in_batch,
            len(issues),
            rate,
        )

        if max_records and total_read >= max_records:
            break

    # 5. Synchronize sequences
    sync_database_sequences()

    # 6. Apply database indexes
    if create_indexes:
        apply_database_indexes()

    total_elapsed = time.time() - start_total_time
    avg_speed = total_loaded / total_elapsed if total_elapsed > 0 else 0

    logger.info("=" * 70)
    logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("=" * 70)
    logger.info("Total Rows Processed:   %s", f"{total_read:,}")
    logger.info("Total Rows Loaded:      %s", f"{total_loaded:,}")
    logger.info("Total Anomalies Flagged:%s (%.2f%%)", f"{total_anomalies:,}", (total_anomalies / total_loaded * 100) if total_loaded else 0)
    logger.info("Quality Issues Created: %s", f"{total_issues:,}")
    logger.info("Total Duration:         %.2f seconds (%.2f minutes)", total_elapsed, total_elapsed / 60)
    logger.info("Overall Throughput:     %.0f rows/second", avg_speed)
    logger.info("=" * 70)

    return {
        "rows_loaded": total_loaded,
        "anomalies": total_anomalies,
        "issues": total_issues,
        "duration_seconds": total_elapsed,
    }


if __name__ == "__main__":
    run_etl_pipeline()
