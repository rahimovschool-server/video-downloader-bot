"""
Hydrogram (Pyrogram fork, Python 3.12+) orqali fayllarni
Telegram kanaliga yuklash. Limit: 2 GB.
"""
import logging
from pathlib import Path

from hydrogram import Client
from hydrogram.types import Message

from config import API_ID, API_HASH, STRING_SESSION, STORAGE_CHANNEL_ID

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            name="media_uploader",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=STRING_SESSION,
            no_updates=True,
            in_memory=True,
        )
    return _client


async def start_client() -> None:
    client = get_client()
    if not client.is_connected:
        await client.start()
        me = await client.get_me()
        logger.info(f"🟢 Hydrogram ulandi: {me.first_name} (@{me.username})")


async def stop_client() -> None:
    global _client
    if _client and _client.is_connected:
        await _client.stop()
        logger.info("🔴 Hydrogram ulanishi yopildi")
    _client = None


async def upload_video(filepath: str, caption: str = "") -> str:
    """Videoni kanalga yuklaydi, file_id qaytaradi (2GB gacha)."""
    client = get_client()
    size = _size_mb(filepath)
    logger.info(f"⬆️ Video: {Path(filepath).name} ({size:.1f} MB)")

    msg: Message = await client.send_video(
        chat_id=STORAGE_CHANNEL_ID,
        video=filepath,
        caption=caption or Path(filepath).stem[:200],
        supports_streaming=True,
        progress=_log_progress,
    )
    fid = msg.video.file_id
    logger.info(f"✅ Video yuklandi → {fid[:20]}...")
    return fid


async def upload_audio(filepath: str, caption: str = "") -> str:
    """Audio (MP3) ni kanalga yuklaydi, file_id qaytaradi."""
    client = get_client()
    size = _size_mb(filepath)
    logger.info(f"⬆️ Audio: {Path(filepath).name} ({size:.1f} MB)")

    msg: Message = await client.send_audio(
        chat_id=STORAGE_CHANNEL_ID,
        audio=filepath,
        caption=caption or Path(filepath).stem[:200],
        title=Path(filepath).stem[:64],
        progress=_log_progress,
    )
    fid = msg.audio.file_id
    logger.info(f"✅ Audio yuklandi → {fid[:20]}...")
    return fid


async def upload_photo(filepath: str, caption: str = "") -> str:
    """Rasmni kanalga yuklaydi, file_id qaytaradi."""
    client = get_client()
    msg: Message = await client.send_photo(
        chat_id=STORAGE_CHANNEL_ID,
        photo=filepath,
        caption=caption,
    )
    return msg.photo.file_id


async def upload_document(filepath: str, caption: str = "") -> str:
    """Har qanday fayl (hujjat) ni kanalga yuklaydi."""
    client = get_client()
    logger.info(f"⬆️ Hujjat: {Path(filepath).name} ({_size_mb(filepath):.1f} MB)")
    msg: Message = await client.send_document(
        chat_id=STORAGE_CHANNEL_ID,
        document=filepath,
        caption=caption or Path(filepath).stem[:200],
        progress=_log_progress,
    )
    return msg.document.file_id


def _size_mb(filepath: str) -> float:
    try:
        return Path(filepath).stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def _log_progress(current: int, total: int) -> None:
    if total and total > 0:
        pct = current * 100 // total
        if pct % 25 == 0:
            logger.info(f"   📤 {pct}% ({current // (1024*1024)}/{total // (1024*1024)} MB)")
