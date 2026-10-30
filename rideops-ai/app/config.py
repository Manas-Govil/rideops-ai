from pathlib import Path
from typing import List, Set
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rideops"

    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # ETL Thresholds & Rules
    MAX_TRIP_DURATION_MINUTES: float = 1440.0   # 24 hours max reasonable duration
    MIN_TRIP_DURATION_MINUTES: float = 0.5      # At least 30 seconds
    MAX_FARE_PER_MILE: float = 500.0           # Extreme fare/mile cutoff
    MIN_PASSENGER_COUNT: int = 1
    MAX_PASSENGER_COUNT: int = 9
    MAX_FARE_AMOUNT: float = 2000.0             # Normal metered maximum
    MAX_TRIP_DISTANCE: float = 500.0            # Max realistic single taxi trip (miles)
    CHUNK_SIZE: int = 100_000                   # Chunk size for batch processing

    # SQL Guardrails & Security
    DEFAULT_ROW_LIMIT: int = 100
    MAX_ROW_LIMIT: int = 1000
    QUERY_TIMEOUT_MS: int = 5000                # 5-second statement timeout

    # Approved tables and views allow-list
    ALLOWED_OBJECTS: Set[str] = {
        "dim_taxi_zones",
        "fact_trips",
        "data_quality_issues",
        "agent_audit_log",
        "v_clean_trips",
        "v_hourly_demand",
        "v_zone_performance",
        "v_quality_issue_summary",
        "rideops.dim_taxi_zones",
        "rideops.fact_trips",
        "rideops.data_quality_issues",
        "rideops.agent_audit_log",
        "rideops.v_clean_trips",
        "rideops.v_hourly_demand",
        "rideops.v_zone_performance",
        "rideops.v_quality_issue_summary",
    }

    @property
    def psycopg2_url(self) -> str:
        """Returns standard postgresql:// URL for psycopg2 driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql://", 1)
        return url

    @property
    def sqlalchemy_url(self) -> str:
        """Returns postgresql+psycopg2:// URL for SQLAlchemy."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
