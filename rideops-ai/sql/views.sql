-- RideOps AI - Analytical Views
-- Designed to accelerate AI Agent queries and enforce consistent business logic.

-- 1. View: Clean Trips with Resolved Zone Names (filters out anomalies)
CREATE OR REPLACE VIEW rideops.v_clean_trips AS
SELECT
    t.trip_id,
    t.pickup_datetime,
    t.dropoff_datetime,
    EXTRACT(HOUR FROM t.pickup_datetime)::INT AS pickup_hour,
    t.pickup_location_id,
    pz.borough AS pickup_borough,
    pz.zone AS pickup_zone,
    t.dropoff_location_id,
    dz.borough AS dropoff_borough,
    dz.zone AS dropoff_zone,
    t.passenger_count,
    t.trip_distance,
    t.fare_amount,
    t.tip_amount,
    t.total_amount,
    t.trip_duration,
    t.fare_per_mile,
    t.tip_percentage,
    t.airport_flag
FROM rideops.fact_trips t
LEFT JOIN rideops.dim_taxi_zones pz ON t.pickup_location_id = pz.location_id
LEFT JOIN rideops.dim_taxi_zones dz ON t.dropoff_location_id = dz.location_id
WHERE t.anomaly_flag = FALSE;


-- 2. View: Hourly Demand & Revenue Patterns
CREATE OR REPLACE VIEW rideops.v_hourly_demand AS
SELECT
    EXTRACT(HOUR FROM pickup_datetime)::INT AS pickup_hour,
    COUNT(*) AS total_trips,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(fare_amount), 2) AS avg_fare,
    ROUND(AVG(trip_distance), 2) AS avg_distance,
    ROUND(AVG(trip_duration), 2) AS avg_duration_minutes,
    COUNT(*) FILTER (WHERE airport_flag = TRUE) AS airport_trips
FROM rideops.fact_trips
WHERE anomaly_flag = FALSE
GROUP BY EXTRACT(HOUR FROM pickup_datetime)::INT
ORDER BY pickup_hour;


-- 3. View: Taxi Zone Performance & Revenue Metrics
CREATE OR REPLACE VIEW rideops.v_zone_performance AS
SELECT
    t.pickup_location_id,
    COALESCE(z.borough, 'Unknown') AS borough,
    COALESCE(z.zone, 'Unknown Zone') AS zone,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount), 2) AS total_revenue,
    ROUND(AVG(t.fare_amount), 2) AS avg_fare,
    ROUND(AVG(t.fare_per_mile), 2) AS avg_fare_per_mile,
    ROUND(AVG(t.tip_percentage), 2) AS avg_tip_percentage
FROM rideops.fact_trips t
LEFT JOIN rideops.dim_taxi_zones z ON t.pickup_location_id = z.location_id
WHERE t.anomaly_flag = FALSE
GROUP BY t.pickup_location_id, z.borough, z.zone
ORDER BY total_revenue DESC;


-- 4. View: Data Quality & Anomaly Summary
CREATE OR REPLACE VIEW rideops.v_quality_issue_summary AS
SELECT
    issue_type,
    severity,
    COUNT(*) AS total_occurrences,
    COUNT(DISTINCT trip_id) AS distinct_trips_affected,
    MIN(description) AS sample_description
FROM rideops.data_quality_issues
GROUP BY issue_type, severity
ORDER BY 
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END,
    total_occurrences DESC;
