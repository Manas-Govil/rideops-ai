from contextlib import contextmanager
from typing import Generator
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from app.config import settings


engine: Engine = create_engine(
    settings.sqlalchemy_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager for raw psycopg2 connections with schema search_path set to rideops."""
    conn = psycopg2.connect(settings.psycopg2_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO rideops, public;")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection() -> bool:
    """Tests connection to PostgreSQL and prints version."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"[OK] Connected to PostgreSQL: {version}")
                return True
    except Exception as exc:
        print(f"[ERROR] Database connection failed: {exc}")
        return False


if __name__ == "__main__":
    test_connection()
