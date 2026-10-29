"""Migration runner for GraphWeave PostgreSQL database."""
import asyncio
import os
import asyncpg
from app.core.config import settings
from app.core.logging import logger


async def run_migrations():
    migration_file = os.path.join(os.path.dirname(__file__), "001_initial_schema.sql")
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    clean_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    logger.info(f"Connecting to database to apply migrations...")
    try:
        conn = await asyncpg.connect(clean_url, timeout=5.0)
        logger.info("Executing 001_initial_schema.sql...")
        await conn.execute(sql)
        await conn.close()
        logger.info("Migrations applied successfully!")
    except Exception as e:
        logger.warning(f"Failed to apply migrations against live database: {e}")
        logger.info("If running in development without PostgreSQL container, in-memory fallback will handle runtime.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
