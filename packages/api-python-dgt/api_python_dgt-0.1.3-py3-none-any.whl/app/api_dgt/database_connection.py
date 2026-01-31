from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def create_postgres_engine(
    env_path: str | Path = "../../variables.env",
    sslmode: str = "require",
    test_connection: bool = True,
) -> Engine:
    """
    Create and return a SQLAlchemy Engine for PostgreSQL using env vars:
    PGHOST, PGUSER, PGPASSWORD, PGPORT (optional), PGDATABASE.

    Notes:
      - Loads variables from env_path via python-dotenv.
      - URL-encodes the password (quote_plus) to avoid issues with special chars.
      - Optionally tests the connection with 'SELECT 1'.
    """
    env_path = Path(env_path)

    if env_path.exists():
        load_dotenv(env_path, override=True)

    pg_host = os.getenv("PGHOST")
    pg_user = os.getenv("PGUSER")
    pg_pass = os.getenv("PGPASSWORD")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE")

    missing = [k for k, v in {
        "PGHOST": pg_host,
        "PGUSER": pg_user,
        "PGPASSWORD": pg_pass,
        "PGDATABASE": pg_db,
    }.items() if not v]

    if missing:
        raise ValueError(
            f"Missing env vars: {missing}. "
            f"Check your environment or the file: {env_path.resolve()}"
        )

    database_url = (
        f"postgresql+psycopg2://{pg_user}:{quote_plus(pg_pass)}@{pg_host}:{pg_port}/{pg_db}"
        f"?sslmode={sslmode}"
    )

    engine = create_engine(database_url, pool_pre_ping=True)

    if test_connection:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))

    return engine