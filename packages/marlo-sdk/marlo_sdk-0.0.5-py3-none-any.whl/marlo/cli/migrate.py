#!/usr/bin/env python3
"""
Database migration script for Marlo.

Usage:
    python -m marlo.cli.migrate

Environment variables:
    DATABASE_URL or MARLO_DATABASE_URL: PostgreSQL connection string
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME: Individual connection params
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

import importlib_resources
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCHEMA_FILES = (
    "sessions.sql",
    "tasks.sql",
    "trajectory.sql",
    "agents.sql",
    "reward.sql",
    "learning.sql",
    "search.sql",
    "copilot.sql",
    "feedback.sql",
)


def get_database_url() -> str:
    """Get database URL from environment variables."""
    for key in ("MARLO_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return value

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_sslmode = os.getenv("DB_SSLMODE")

    if db_host and db_port and db_user and db_password and db_name:
        url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        if db_sslmode:
            url += f"?sslmode={db_sslmode}"
        return url

    raise RuntimeError(
        "DATABASE_URL or DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME are required."
    )


async def run_migrations(database_url: str) -> None:
    """Run all database migrations."""
    try:
        import asyncpg
    except ImportError as exc:
        logger.error("asyncpg is required for database migrations")
        raise RuntimeError("asyncpg not installed") from exc

    logger.info("Connecting to database...")
    connection = await asyncpg.connect(dsn=database_url)

    try:
        base = importlib_resources.files("marlo.storage.postgres")

        for filename in SCHEMA_FILES:
            logger.info("Applying schema: %s", filename)
            sql_content = base.joinpath(filename).read_text(encoding="utf-8")
            await connection.execute(sql_content)
            logger.info("Successfully applied: %s", filename)

        logger.info("All migrations completed successfully")

    finally:
        await connection.close()
        logger.info("Database connection closed")


def main() -> int:
    """Main entry point."""
    try:
        database_url = get_database_url()
        logger.info("Starting database migrations...")
        asyncio.run(run_migrations(database_url))
        return 0
    except Exception as exc:
        logger.error("Migration failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
