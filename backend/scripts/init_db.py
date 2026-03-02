#!/usr/bin/env python3
"""
SAWS Database Initialization Script

Creates the database, extensions, and initializes all tables.
Run this before starting the application for the first time.

Usage:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.config import get_settings
from app.db.base import Base, async_engine

settings = get_settings()


async def create_database():
    """
    Create the database if it doesn't exist.

    Connects to PostgreSQL default database to create SAWS database.
    """
    # Parse database URL to get connection details
    db_url = settings.database_url
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    db_url_clean = db_url.replace("postgresql+asyncpg://", "postgresql://")

    # Extract connection info
    import re
    match = re.match(
        r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<db>.+)",
        db_url_clean
    )

    if not match:
        print(f"Error: Could not parse database URL: {db_url}")
        return False

    user = match.group("user")
    password = match.group("password")
    host = match.group("host")
    port = int(match.group("port"))
    target_db = match.group("db")

    print(f"Connecting to PostgreSQL at {host}:{port}...")

    try:
        # Connect to 'postgres' database to create our database
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT datname FROM pg_database WHERE datname = $1)",
            target_db
        )

        if exists:
            print(f"Database '{target_db}' already exists.")
        else:
            # Create database
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            print(f"✓ Created database '{target_db}'")

        await conn.close()
        return True

    except Exception as e:
        print(f"Error creating database: {e}")
        print("\nNote: Make sure PostgreSQL is running and credentials are correct.")
        return False


async def create_extensions():
    """
    Create required PostgreSQL extensions.

    Creates PostGIS and TimescaleDB extensions.
    """
    print("\nCreating PostgreSQL extensions...")

    try:
        async with async_engine.begin() as conn:
            # Create PostGIS extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            print("✓ PostGIS extension created")

            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology"))
            print("✓ PostGIS Topology extension created")

            # Try to create TimescaleDB (optional - may not be installed)
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                print("✓ TimescaleDB extension created")
            except Exception:
                print("⚠ TimescaleDB not available (optional for development)")

        return True

    except Exception as e:
        print(f"Error creating extensions: {e}")
        return False


async def create_tables():
    """
    Create all database tables from SQLAlchemy models.

    Imports all models to ensure they're registered with Base.metadata.
    """
    print("\nCreating database tables...")

    try:
        # Import all models to register them
        from app.models import field, alert, satellite, weather

        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✓ All tables created successfully")
        return True

    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


async def verify_setup():
    """
    Verify the database setup is working.
    """
    print("\nVerifying database setup...")

    try:
        async with async_engine.connect() as conn:
            # Check PostGIS version
            result = await conn.execute(text("SELECT PostGIS_Version()"))
            postgis_version = result.scalar()
            print(f"✓ PostGIS version: {postgis_version}")

            # Check spatial_ref_sys table
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM spatial_ref_sys WHERE srid = 4326"
            ))
            count = result.scalar()
            if count > 0:
                print("✓ Spatial reference system (EPSG:4326) loaded")
            else:
                print("⚠ Warning: EPSG:4326 not found in spatial_ref_sys")

            # List tables
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"✓ Tables created: {', '.join(tables) if tables else 'None'}")

        return True

    except Exception as e:
        print(f"Warning: Could not verify setup: {e}")
        return False


async def main():
    """
    Main initialization function.
    """
    print("=" * 60)
    print("SAWS Database Initialization")
    print("=" * 60)
    print(f"Database: {settings.database_url.split('/')[-1]}")
    print(f"Host: {settings.db_host}")
    print("=" * 60)

    success = True

    # Step 1: Create database
    if not await create_database():
        success = False

    # Step 2: Create extensions
    if not await create_extensions():
        success = False

    # Step 3: Create tables
    if not await create_tables():
        success = False

    # Step 4: Verify setup
    await verify_setup()

    print("\n" + "=" * 60)
    if success:
        print("✓ Database initialization complete!")
        print("\nNext steps:")
        print("  1. Run: python scripts/seed_data.py")
        print("  2. Start the server: uvicorn app.main:app --reload")
    else:
        print("✗ Database initialization failed. Please check the errors above.")
        sys.exit(1)

    print("=" * 60)

    # Close connections
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
