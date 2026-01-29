"""SQLite connection management.

Provides instance-aware database path and async connection context manager.
Each BPA instance gets its own isolated database.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

from mcp_eregistrations_bpa.config import get_instance_data_dir


def get_db_path() -> Path:
    """Get instance-specific database path.

    Returns the path to the SQLite database file for the current BPA instance.
    Each instance (El Salvador, Cuba, etc.) gets its own database.

    Path pattern:
        ~/.config/mcp-eregistrations-bpa/instances/{instance-slug}/data.db

    Falls back to legacy path if no instance configured:
        ~/.config/mcp-eregistrations-bpa/data.db

    Creates the parent directory if it doesn't exist.

    Returns:
        Path to the instance-specific database file.
    """
    instance_dir = get_instance_data_dir()
    return instance_dir / "data.db"


@asynccontextmanager
async def get_connection(
    db_path: Path | None = None,
) -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get async SQLite connection with WAL mode and foreign keys enabled.

    Args:
        db_path: Optional path to database. Defaults to get_db_path() if not provided.

    Yields:
        Configured aiosqlite connection with Row factory.

    Example:
        async with get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM audit_logs")
            rows = await cursor.fetchall()
    """
    if db_path is None:
        db_path = get_db_path()

    async with aiosqlite.connect(db_path) as conn:
        # Enable WAL mode for better concurrent access
        await conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key enforcement
        await conn.execute("PRAGMA foreign_keys=ON")
        # Use Row factory for dict-like access
        conn.row_factory = aiosqlite.Row
        yield conn
