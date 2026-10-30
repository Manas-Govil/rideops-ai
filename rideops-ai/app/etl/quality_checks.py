import logging
from typing import List, Set, Tuple
import numpy as np
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)


def evaluate_data_quality(
    df: pd.DataFrame,
    valid_zone_ids: Set[int]
) -> Tuple[pd.Series, List[Tuple[int, str, str, str]]]:
    """
    Evaluates data quality rules on a DataFrame of transformed trips.

    Returns:
        anomaly_flags: pd.Series of booleans indicating if the trip is an anomaly.
        quality_issues: List of tuples (trip_id, issue_type, severity, description).
    """
    n = len(df)
    anomaly_flags = pd.Series(False, index=df.index)
    quality_issues: List[Tuple[int, str, str, str]] = []

    trip_ids = df["trip_id"].to_numpy()

    # 1. CRITICAL CHECKS (Severe financial or temporal corruptions)
    neg_fare_mask = (df["fare_amount"] < 0).to_numpy()
    if np.any(neg_fare_mask):
        anomaly_flags |= neg_fare_mask
        for tid, val in zip(trip_ids[neg_fare_mask], df.loc[neg_fare_mask, "fare_amount"]):
            quality_issues.append((int(tid), "NEGATIVE_FARE", "CRITICAL", f"Negative fare amount: ${val:.2f}"))

    neg_total_mask = (df["total_amount"] < 0).to_numpy()
    if np.any(neg_total_mask):
        anomaly_flags |= neg_total_mask
        for tid, val in zip(trip_ids[neg_total_mask], df.loc[neg_total_mask, "total_amount"]):
            quality_issues.append((int(tid), "NEGATIVE_TOTAL", "CRITICAL", f"Negative total amount: ${val:.2f}"))

    inverted_time_mask = (df["dropoff_datetime"] < df["pickup_datetime"]).to_numpy()
    if np.any(inverted_time_mask):
        anomaly_flags |= inverted_time_mask
        for tid in trip_ids[inverted_time_mask]:
            quality_issues.append((int(tid), "INVERTED_TIMESTAMPS", "CRITICAL", "Dropoff datetime is earlier than pickup datetime"))

    # 2. HIGH SEVERITY CHECKS (Outliers and extreme physical / financial anomalies)
    extreme_fare_mask = (df["fare_amount"] > settings.MAX_FARE_AMOUNT).to_numpy()
    if np.any(extreme_fare_mask):
        anomaly_flags |= extreme_fare_mask
        for tid, val in zip(trip_ids[extreme_fare_mask], df.loc[extreme_fare_mask, "fare_amount"]):
            quality_issues.append((int(tid), "EXTREME_FARE", "HIGH", f"Fare amount ${val:.2f} exceeds threshold of ${settings.MAX_FARE_AMOUNT:.2f}"))

    extreme_dist_mask = (df["trip_distance"] > settings.MAX_TRIP_DISTANCE).to_numpy()
    if np.any(extreme_dist_mask):
        anomaly_flags |= extreme_dist_mask
        for tid, val in zip(trip_ids[extreme_dist_mask], df.loc[extreme_dist_mask, "trip_distance"]):
            quality_issues.append((int(tid), "EXTREME_DISTANCE", "HIGH", f"Trip distance {val:.2f} miles exceeds threshold of {settings.MAX_TRIP_DISTANCE} miles"))

    extreme_duration_mask = (df["trip_duration"] > settings.MAX_TRIP_DURATION_MINUTES).to_numpy()
    if np.any(extreme_duration_mask):
        anomaly_flags |= extreme_duration_mask
        for tid, val in zip(trip_ids[extreme_duration_mask], df.loc[extreme_duration_mask, "trip_duration"]):
            quality_issues.append((int(tid), "EXTREME_DURATION", "HIGH", f"Trip duration {val:.1f} minutes exceeds threshold of {settings.MAX_TRIP_DURATION_MINUTES} minutes"))

    fare_per_mile_vals = df["fare_per_mile"].fillna(0).to_numpy()
    extreme_fpm_mask = (fare_per_mile_vals > settings.MAX_FARE_PER_MILE)
    if np.any(extreme_fpm_mask):
        anomaly_flags |= extreme_fpm_mask
        for tid, val in zip(trip_ids[extreme_fpm_mask], fare_per_mile_vals[extreme_fpm_mask]):
            quality_issues.append((int(tid), "EXTREME_FARE_PER_MILE", "HIGH", f"Fare per mile ${val:.2f} exceeds threshold of ${settings.MAX_FARE_PER_MILE:.2f}"))

    # 3. MEDIUM SEVERITY CHECKS (Invalid operational fields)
    neg_dist_mask = (df["trip_distance"] < 0).to_numpy()
    if np.any(neg_dist_mask):
        anomaly_flags |= neg_dist_mask
        for tid, val in zip(trip_ids[neg_dist_mask], df.loc[neg_dist_mask, "trip_distance"]):
            quality_issues.append((int(tid), "NEGATIVE_DISTANCE", "MEDIUM", f"Negative trip distance: {val:.3f} miles"))

    zero_dist_with_fare = ((df["trip_distance"] == 0) & (df["fare_amount"] > 10.0)).to_numpy()
    if np.any(zero_dist_with_fare):
        anomaly_flags |= zero_dist_with_fare
        for tid, val in zip(trip_ids[zero_dist_with_fare], df.loc[zero_dist_with_fare, "fare_amount"]):
            quality_issues.append((int(tid), "ZERO_DISTANCE_WITH_FARE", "MEDIUM", f"Zero distance recorded for trip with substantial fare: ${val:.2f}"))

    # Passenger count: null, 0, or greater than max
    passenger_series = df["passenger_count"]
    invalid_pass_mask = (
        passenger_series.isna()
        | (passenger_series < settings.MIN_PASSENGER_COUNT)
        | (passenger_series > settings.MAX_PASSENGER_COUNT)
    ).to_numpy()
    if np.any(invalid_pass_mask):
        anomaly_flags |= invalid_pass_mask
        for tid, val in zip(trip_ids[invalid_pass_mask], passenger_series[invalid_pass_mask]):
            val_str = "NULL" if pd.isna(val) else str(int(val))
            quality_issues.append((int(tid), "INVALID_PASSENGER_COUNT", "MEDIUM", f"Passenger count {val_str} outside valid range [{settings.MIN_PASSENGER_COUNT}, {settings.MAX_PASSENGER_COUNT}]"))

    # 4. LOW SEVERITY CHECKS (Minor warnings, short trips, unmapped zones)
    short_duration_mask = ((df["trip_duration"] >= 0) & (df["trip_duration"] < settings.MIN_TRIP_DURATION_MINUTES) & (df["fare_amount"] > 5.0)).to_numpy()
    if np.any(short_duration_mask):
        for tid, val in zip(trip_ids[short_duration_mask], df.loc[short_duration_mask, "trip_duration"]):
            quality_issues.append((int(tid), "VERY_SHORT_DURATION", "LOW", f"Trip duration under 30s ({val:.2f} min) with fare"))

    if valid_zone_ids:
        pu_locs = df["pickup_location_id"].to_numpy()
        unmapped_pu = df["pickup_location_id"].notna().to_numpy() & ~np.isin(pu_locs, list(valid_zone_ids))
        if np.any(unmapped_pu):
            for tid, zid in zip(trip_ids[unmapped_pu], pu_locs[unmapped_pu]):
                quality_issues.append((int(tid), "UNMAPPED_PICKUP_ZONE", "LOW", f"Pickup location ID {int(zid)} not found in dim_taxi_zones"))

        do_locs = df["dropoff_location_id"].to_numpy()
        unmapped_do = df["dropoff_location_id"].notna().to_numpy() & ~np.isin(do_locs, list(valid_zone_ids))
        if np.any(unmapped_do):
            for tid, zid in zip(trip_ids[unmapped_do], do_locs[unmapped_do]):
                quality_issues.append((int(tid), "UNMAPPED_DROPOFF_ZONE", "LOW", f"Dropoff location ID {int(zid)} not found in dim_taxi_zones"))

    return anomaly_flags, quality_issues
