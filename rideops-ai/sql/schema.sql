CREATE SCHEMA IF NOT EXISTS rideops;

CREATE TABLE IF NOT EXISTS rideops.dim_taxi_zones (
    location_id INTEGER PRIMARY KEY,
    borough VARCHAR(100),
    zone VARCHAR(255),
    service_zone VARCHAR(100)
);


CREATE TABLE IF NOT EXISTS rideops.fact_trips (
    trip_id BIGSERIAL PRIMARY KEY,

    vendor_id INTEGER,

    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,

    passenger_count INTEGER,

    trip_distance NUMERIC(12, 3),

    ratecode_id INTEGER,

    pickup_location_id INTEGER,
    dropoff_location_id INTEGER,

    payment_type INTEGER,

    fare_amount NUMERIC(12, 2),
    extra NUMERIC(12, 2),
    mta_tax NUMERIC(12, 2),
    tip_amount NUMERIC(12, 2),
    tolls_amount NUMERIC(12, 2),
    improvement_surcharge NUMERIC(12, 2),
    congestion_surcharge NUMERIC(12, 2),
    airport_fee NUMERIC(12, 2),
    cbd_congestion_fee NUMERIC(12, 2),
    total_amount NUMERIC(12, 2),

    trip_duration NUMERIC(12, 2),
    fare_per_mile NUMERIC(12, 4),
    tip_percentage NUMERIC(12, 4),

    airport_flag BOOLEAN DEFAULT FALSE,
    anomaly_flag BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS rideops.agent_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    user_question TEXT NOT NULL,
    agent_route VARCHAR(100),

    generated_sql TEXT,

    execution_status VARCHAR(50),
    rows_returned INTEGER DEFAULT 0,

    latency_ms NUMERIC(12, 2),

    answer TEXT
);