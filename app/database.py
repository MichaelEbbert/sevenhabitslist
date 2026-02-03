import aiosqlite
import os
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "data" / "sevenhabits.db"

async def get_db():
    """Get database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    """Initialize database tables."""
    os.makedirs(DATABASE_PATH.parent, exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create roles table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)

        # Create tasks table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                effort_level TEXT NOT NULL CHECK (effort_level IN ('Low', 'Medium', 'High')),
                scheduled_date DATE,
                is_complete INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        """)

        await db.commit()
