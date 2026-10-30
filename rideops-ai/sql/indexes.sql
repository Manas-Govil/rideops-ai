-- RideOps AI - Database Performance Indexes
-- NOTE: Create these indexes AFTER bulk loading fact_trips to maximize ingestion speed.

-- 1. Fact Trips Indexes
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_datetime
    ON rideops.fact_trips (pickup_datetime);

CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_location_id
    ON rideops.fact_trips (pickup_location_id);

CREATE INDEX IF NOT EXISTS idx_fact_trips_dropoff_location_id
    ON rideops.fact_trips (dropoff_location_id);

CREATE INDEX IF NOT EXISTS idx_fact_trips_airport_flag
    ON rideops.fact_trips (airport_flag);

CREATE INDEX IF NOT EXISTS idx_fact_trips_anomaly_flag
    ON rideops.fact_trips (anomaly_flag);

-- 2. Data Quality Issues Indexes
CREATE INDEX IF NOT EXISTS idx_data_quality_issues_trip_id
    ON rideops.data_quality_issues (trip_id);

CREATE INDEX IF NOT EXISTS idx_data_quality_issues_severity
    ON rideops.data_quality_issues (severity);

CREATE INDEX IF NOT EXISTS idx_data_quality_issues_issue_type
    ON rideops.data_quality_issues (issue_type);
