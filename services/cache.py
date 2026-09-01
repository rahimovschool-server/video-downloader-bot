"""
SQLite kesh: URL + quality → Telegram file_id
Bir marta yuklangan faylni qayta yuklamasdan file_id orqali yuborish.
"""
import aiosqlite
import logging
import os

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("downloads", "cache.db")
os.makedirs("downloads", exist_ok=True)


async def init_db() -> None:
    """Jadvalni yaratish (bot ishga tushganda chaqiriladi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS file_cache (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url         TEXT NOT NULL,
                quality     TEXT NOT NULL,
                media_type  TEXT NOT NULL,        -- 'video' | 'audio' | 'image'
                file_id     TEXT NOT NULL,
                file_size   REAL DEFAULT 0,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url, quality, media_type)
            )
        """)
        await db.commit()
    logger.info("✅ SQLite kesh bazasi tayyor")


async def get_cached(url: str, quality: str, media_type: str) -> str | None:
    """
    Keshdan file_id olish.
    Topilmasa None qaytaradi.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id FROM file_cache WHERE url=? AND quality=? AND media_type=?",
            (url, quality, media_type),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def save_cache(
    url: str,
    quality: str,
    media_type: str,
    file_id: str,
    file_size: float = 0.0,
) -> None:
    """file_id ni keshga saqlash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO file_cache
                (url, quality, media_type, file_id, file_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (url, quality, media_type, file_id, file_size),
        )
        await db.commit()
    logger.info(f"💾 Keshga saqlandi: {media_type} | {quality} | size={file_size:.1f}MB")


async def get_cache_stats() -> dict:
    """Kesh statistikasi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM file_cache") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT SUM(file_size) FROM file_cache") as cur:
            total_size = (await cur.fetchone())[0] or 0
    return {"total": total, "total_size_mb": round(total_size, 1)}
