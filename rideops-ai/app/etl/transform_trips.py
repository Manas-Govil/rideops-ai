import logging
from typing import Set, Tuple, List
import numpy as np
import pandas as pd
from app.etl.quality_checks import evaluate_data_quality

logger = logging.getLogger(__name__)


def transform_trip_batch(
    raw_df: pd.DataFrame,
    start_trip_id: int,
    valid_zone_ids: Set[int],
    airport_zone_ids: Set[int]
) -> Tuple[pd.DataFrame, List[Tuple[int, str, str, str]]]:
    """
    Transforms a raw parquet batch into the RideOps fact_trips format,
    computes derived metrics, and evaluates data quality rules.

    Args:
        raw_df: Raw batch DataFrame from parquet.
        start_trip_id: Starting integer for assigning sequential trip_id.
        valid_zone_ids: Set of valid location_id values from dim_taxi_zones.
        airport_zone_ids: Set of airport location_id values (e.g. {1, 132, 138}).

    Returns:
        transformed_df: Cleaned DataFrame conforming to fact_trips schema.
        quality_issues: List of data quality issue tuples.
    """
    batch_size = len(raw_df)
    df = pd.DataFrame(index=raw_df.index)

    # 1. Assign sequential trip_id
    df["trip_id"] = np.arange(start_trip_id, start_trip_id + batch_size, dtype=np.int64)

    # 2. Datetimes and temporal metrics
    df["pickup_datetime"] = pd.to_datetime(raw_df["tpep_pickup_datetime"])
    df["dropoff_datetime"] = pd.to_datetime(raw_df["tpep_dropoff_datetime"])

    # Duration in minutes
    duration_minutes = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds() / 60.0
    df["trip_duration"] = duration_minutes.round(2)

    # 3. Location IDs
    df["pickup_location_id"] = pd.to_numeric(raw_df["PULocationID"], errors="coerce").astype("Int64")
    df["dropoff_location_id"] = pd.to_numeric(raw_df["DOLocationID"], errors="coerce").astype("Int64")

    # 4. Operational and financial attributes
    df["passenger_count"] = pd.to_numeric(raw_df["passenger_count"], errors="coerce").astype("Int64")
    df["trip_distance"] = pd.to_numeric(raw_df["trip_distance"], errors="coerce").round(3)
    df["fare_amount"] = pd.to_numeric(raw_df["fare_amount"], errors="coerce").round(2)
    df["tip_amount"] = pd.to_numeric(raw_df["tip_amount"], errors="coerce").round(2)
    df["total_amount"] = pd.to_numeric(raw_df["total_amount"], errors="coerce").round(2)

    # 5. Derived metrics: fare_per_mile and tip_percentage
    # Avoid zero division and guard against numeric overflow (> 99999999 for NUMERIC(12,4))
    valid_distance = (df["trip_distance"] > 0)
    fare_per_mile = np.where(valid_distance, df["fare_amount"] / df["trip_distance"], np.nan)
    # Cap astronomical values to NaN so database doesn't overflow, while quality check flags them
    fare_per_mile = np.where(np.abs(fare_per_mile) < 99_999_999, fare_per_mile, np.nan)
    df["fare_per_mile"] = np.round(fare_per_mile, 4)

    valid_fare = (df["fare_amount"] > 0)
    tip_pct = np.where(valid_fare, (df["tip_amount"] / df["fare_amount"]) * 100.0, np.nan)
    tip_pct = np.where(np.abs(tip_pct) < 99_999_999, tip_pct, np.nan)
    df["tip_percentage"] = np.round(tip_pct, 4)

    # 6. Airport flag
    # Check if pickup or dropoff is an airport, or Airport_fee > 0
    is_airport_pu = df["pickup_location_id"].isin(airport_zone_ids)
    is_airport_do = df["dropoff_location_id"].isin(airport_zone_ids)
    has_airport_fee = pd.to_numeric(raw_df.get("Airport_fee", 0), errors="coerce").fillna(0) > 0
    df["airport_flag"] = (is_airport_pu | is_airport_do | has_airport_fee).astype(bool)

    # 7. Evaluate data quality rules & anomaly detection
    anomaly_flags, quality_issues = evaluate_data_quality(df, valid_zone_ids)
    df["anomaly_flag"] = anomaly_flags.astype(bool)

    # 8. Align column order exactly with rideops.fact_trips
    target_columns = [
        "trip_id",
        "pickup_datetime",
        "dropoff_datetime",
        "pickup_location_id",
        "dropoff_location_id",
        "passenger_count",
        "trip_distance",
        "fare_amount",
        "tip_amount",
        "total_amount",
        "trip_duration",
        "fare_per_mile",
        "tip_percentage",
        "airport_flag",
        "anomaly_flag",
    ]
    df = df[target_columns]

    return df, quality_issues
