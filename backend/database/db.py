import aiosqlite
import os
from pathlib import Path

DB_PATH = Path(os.getenv("DB_PATH", str(Path(__file__).parent.parent / "energy.db")))


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS consumption (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                watts_total REAL NOT NULL,
                kwh_cumulative REAL NOT NULL,
                is_charging INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS epex_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_start TEXT NOT NULL UNIQUE,
                price_eur_mwh REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS charging_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                kwh_total REAL DEFAULT 0,
                cost_eur REAL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bmw_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                battery_percent INTEGER,
                range_km INTEGER,
                charging_status TEXT
            )
        """)
        await db.commit()
