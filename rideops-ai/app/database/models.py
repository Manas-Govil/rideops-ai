from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    Boolean,
    DateTime,
    Text,
    func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DimTaxiZone(Base):
    __tablename__ = "dim_taxi_zones"
    __table_args__ = {"schema": "rideops"}

    location_id = Column(Integer, primary_key=True)
    borough = Column(String(100), nullable=True)
    zone = Column(String(255), nullable=True)
    service_zone = Column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<DimTaxiZone(id={self.location_id}, borough='{self.borough}', zone='{self.zone}')>"


class FactTrip(Base):
    __tablename__ = "fact_trips"
    __table_args__ = {"schema": "rideops"}

    trip_id = Column(BigInteger, primary_key=True, autoincrement=True)
    pickup_datetime = Column(DateTime, nullable=False)
    dropoff_datetime = Column(DateTime, nullable=False)

    pickup_location_id = Column(Integer, nullable=True)
    dropoff_location_id = Column(Integer, nullable=True)

    passenger_count = Column(Integer, nullable=True)
    trip_distance = Column(Numeric(12, 3), nullable=True)

    fare_amount = Column(Numeric(12, 2), nullable=True)
    tip_amount = Column(Numeric(12, 2), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)

    trip_duration = Column(Numeric(12, 2), nullable=True)
    fare_per_mile = Column(Numeric(12, 4), nullable=True)
    tip_percentage = Column(Numeric(12, 4), nullable=True)

    airport_flag = Column(Boolean, default=False)
    anomaly_flag = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<FactTrip(id={self.trip_id}, fare={self.fare_amount}, anomaly={self.anomaly_flag})>"


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"
    __table_args__ = {"schema": "rideops"}

    issue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    trip_id = Column(BigInteger, nullable=True)
    issue_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    detected_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<DataQualityIssue(id={self.issue_id}, type='{self.issue_type}', severity='{self.severity}')>"


class AgentAuditLog(Base):
    __tablename__ = "agent_audit_log"
    __table_args__ = {"schema": "rideops"}

    audit_id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, server_default=func.now())
    user_question = Column(Text, nullable=False)
    agent_route = Column(String(100), nullable=True)
    generated_sql = Column(Text, nullable=True)
    execution_status = Column(String(50), nullable=True)
    rows_returned = Column(Integer, default=0)
    latency_ms = Column(Numeric(12, 2), nullable=True)
    answer = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentAuditLog(id={self.audit_id}, route='{self.agent_route}', status='{self.execution_status}')>"
