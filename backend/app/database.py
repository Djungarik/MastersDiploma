"""
Database setup for Adaptive OST
Uses SQLite for simple, file-based user storage
"""

import aiosqlite
import os
from contextlib import asynccontextmanager

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "adaptive_ost.db")


async def init_db():
    """Initialize the database with required tables"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Create user preferences table (for future use)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                default_mood TEXT DEFAULT 'calm',
                default_environment TEXT DEFAULT 'tavern',
                volume REAL DEFAULT 0.7,
                analysis_interval INTEGER DEFAULT 20000,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        await db.commit()
        print("✅ Database initialized")


@asynccontextmanager
async def get_db():
    """Get database connection"""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def get_user_by_email(email: str) -> dict | None:
    """Get user by email"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def get_user_by_id(user_id: int) -> dict | None:
    """Get user by ID"""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None


async def create_user(email: str, username: str, hashed_password: str) -> dict:
    """Create a new user"""
    async with get_db() as db:
        cursor = await db.execute(
            "INSERT INTO users (email, username, hashed_password) VALUES (?, ?, ?)",
            (email, username, hashed_password)
        )
        await db.commit()
        user_id = cursor.lastrowid
        
        # Create default preferences
        await db.execute(
            "INSERT INTO user_preferences (user_id) VALUES (?)",
            (user_id,)
        )
        await db.commit()
        
        return await get_user_by_id(user_id)
