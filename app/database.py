import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiosqlite
from app.config import Config

class Database:
    def __init__(self):
        self.conn = None

    async def init(self):
        # Поддержка SQLite и PostgreSQL через DATABASE_URL (можно расширить)
        if Config.DATABASE_URL.startswith("sqlite"):
            self.conn = await aiosqlite.connect(Config.DATABASE_URL.replace("sqlite:///", ""))
            await self._create_tables_sqlite()
        else:
            # Для PostgreSQL используем asyncpg (здесь упрощённо, можно реализовать отдельно)
            raise NotImplementedError("PostgreSQL support requires asyncpg, implement separately")

    async def _create_tables_sqlite(self):
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                mode TEXT DEFAULT 'analytics',
                min_rating REAL DEFAULT 70.0,
                budget_limit REAL DEFAULT 1000.0,
                blacklist TEXT DEFAULT '[]',
                paused BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS lots (
                id TEXT PRIMARY KEY,
                name TEXT,
                collection TEXT,
                price REAL,
                currency TEXT,
                url TEXT,
                image TEXT,
                created_at TIMESTAMP,
                analyzed_at TIMESTAMP,
                profit REAL,
                rating REAL,
                risk REAL,
                notified BOOLEAN DEFAULT 0,
                user_confirmed BOOLEAN DEFAULT 0
            )
        """)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                date DATE PRIMARY KEY,
                total_lots INTEGER,
                avg_profit REAL,
                avg_rating REAL,
                total_profit REAL
            )
        """)
        await self.conn.commit()

    # ---- Пользователи ----
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = await self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return {
                "user_id": row[0],
                "mode": row[1],
                "min_rating": row[2],
                "budget_limit": row[3],
                "blacklist": json.loads(row[4]),
                "paused": bool(row[5]),
                "created_at": row[6]
            }
        return None

    async def create_user(self, user_id: int, mode: str = "analytics"):
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (user_id, mode) VALUES (?, ?)",
            (user_id, mode)
        )
        await self.conn.commit()

    async def update_user(self, user_id: int, **kwargs):
        fields = []
        values = []
        for k, v in kwargs.items():
            if k == "blacklist":
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
        await self.conn.execute(query, values)
        await self.conn.commit()

    # ---- Лоты ----
    async def save_lot(self, lot: Dict, analysis: Dict):
        await self.conn.execute("""
            INSERT OR REPLACE INTO lots (id, name, collection, price, currency, url, image, created_at, analyzed_at,
                                         profit, rating, risk, notified, user_confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lot["id"], lot["name"], lot["collection"], lot["price"], lot["currency"],
            lot["url"], lot.get("image"), lot["created_at"], datetime.utcnow().isoformat(),
            analysis.get("profit", 0.0), analysis.get("rating", 0.0), analysis.get("risk", 0.0),
            0, 0
        ))
        await self.conn.commit()

    async def mark_notified(self, lot_id: str):
        await self.conn.execute("UPDATE lots SET notified = 1 WHERE id = ?", (lot_id,))
        await self.conn.commit()

    async def mark_confirmed(self, lot_id: str):
        await self.conn.execute("UPDATE lots SET user_confirmed = 1 WHERE id = ?", (lot_id,))
        await self.conn.commit()

    async def get_lot(self, lot_id: str):
        cursor = await self.conn.execute("SELECT * FROM lots WHERE id = ?", (lot_id,))
        return await cursor.fetchone()

    # ---- Статистика ----
    async def update_daily_stats(self, date: str, lots_count: int, total_profit: float, avg_rating: float):
        await self.conn.execute("""
            INSERT OR REPLACE INTO stats (date, total_lots, avg_profit, avg_rating, total_profit)
            VALUES (?, ?, ?, ?, ?)
        """, (date, lots_count, total_profit / lots_count if lots_count else 0, avg_rating, total_profit))
        await self.conn.commit()

    async def get_stats(self, days: int = 1):
        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        cursor = await self.conn.execute(
            "SELECT * FROM stats WHERE date >= ? ORDER BY date", (since,)
        )
        rows = await cursor.fetchall()
        return rows

    async def close(self):
        if self.conn:
            await self.conn.close()
