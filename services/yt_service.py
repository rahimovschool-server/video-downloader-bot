import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, AsyncGenerator

import yt_dlp

from config import DOWNLOAD_DIR, PLAYLIST_MAX_ITEMS

logger = logging.getLogger(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ─── Ma'lumot olish ───────────────────────────────────────────────────────────

async def get_video_info(url: str) -> Optional[dict]:
    """Video yoki playlist haqida ma'lumot olish."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "flat_playlist": True,
        "extractor_args": {"youtube": ["player_client=android", "player_skip=webpage"]},
        "geo_bypass": True,
        "nocheckcertificate": True,
    }
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=False)
            )
        return info
    except Exception as e:
        logger.error(f"Info olishda xato: {e}")
        return None


# ─── Bitta video ─────────────────────────────────────────────────────────────

async def download_video(url: str, quality: str, chat_id: int) -> Optional[str]:
    """
    Videoni yuklash. Limit yo'q — Pyrogram yuklaydi.
    quality: '2160' | '1080' | '720' | '480' | '360'
    """
    fmt = (
        f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={quality}]+bestaudio/"
        f"best[height<={quality}]/best"
    )
    opts = {
        "format": fmt,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{chat_id}_%(id)s_%(title).40s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 60,
        "retries": 5,
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "extractor_args": {"youtube": ["player_client=android", "player_skip=webpage"]},
        "geo_bypass": True,
        "nocheckcertificate": True,
    }
    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"
    return await _download_single(url, opts, chat_id, ext=".mp4")


async def download_audio(url: str, quality: str, chat_id: int) -> Optional[str]:
    """
    Audio MP3 yuklash.
    quality: '320' | '192' | '128'
    """
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{chat_id}_%(id)s_%(title).40s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 60,
        "retries": 5,
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata", "add_metadata": True},
        ],
        "extractor_args": {"youtube": ["player_client=android", "player_skip=webpage"]},
        "geo_bypass": True,
        "nocheckcertificate": True,
    }
    if os.path.exists("cookies.txt"):
        opts["cookiefile"] = "cookies.txt"
    return await _download_single(url, opts, chat_id, ext=".mp3")


# ─── PLAYLIST ─────────────────────────────────────────────────────────────────

async def playlist_download_videos(
    url: str, quality: str, chat_id: int
) -> AsyncGenerator[tuple[str, str, int, int], None]:
    """
    Playlist videolarini birin-ketin yuklash.
    Yields: (filepath, title, current_index, total)
    PLAYLIST_MAX_ITEMS=0 → cheksiz
    """
    entries, total = await _get_playlist_entries(url)
    if not entries:
        # Bitta video
        info = await get_video_info(url)
        title = (info or {}).get("title", "Video")
        fp = await download_video(url, quality, chat_id)
        if fp:
            yield fp, title, 1, 1
        return

    limit = PLAYLIST_MAX_ITEMS if PLAYLIST_MAX_ITEMS > 0 else total
    logger.info(f"📋 Playlist: {total} video, limit={limit}")

    for i, entry in enumerate(entries[:limit], 1):
        video_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
        title = entry.get("title", f"Video {i}")
        if not video_url:
            continue
        # agar faqat id bo'lsa, YouTube URL yasaymiz
        if not video_url.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"

        logger.info(f"[{i}/{limit}] 🎬 {title}")
        fp = await download_video(video_url, quality, chat_id)
        if fp:
            yield fp, title, i, limit
        else:
            logger.warning(f"[{i}] ⚠️ yuklab bo'lmadi: {title}")


async def playlist_download_audio(
    url: str, quality: str, chat_id: int
) -> AsyncGenerator[tuple[str, str, int, int], None]:
    """
    Playlist audiolarini birin-ketin yuklash.
    Yields: (filepath, title, current_index, total)
    """
    entries, total = await _get_playlist_entries(url)
    if not entries:
        info = await get_video_info(url)
        title = (info or {}).get("title", "Audio")
        fp = await download_audio(url, quality, chat_id)
        if fp:
            yield fp, title, 1, 1
        return

    limit = PLAYLIST_MAX_ITEMS if PLAYLIST_MAX_ITEMS > 0 else total
    logger.info(f"📋 Playlist: {total} audio, limit={limit}")

    for i, entry in enumerate(entries[:limit], 1):
        video_url = entry.get("url") or entry.get("webpage_url") or entry.get("id")
        title = entry.get("title", f"Audio {i}")
        if not video_url:
            continue
        if not video_url.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"

        logger.info(f"[{i}/{limit}] 🎵 {title}")
        fp = await download_audio(video_url, quality, chat_id)
        if fp:
            yield fp, title, i, limit
        else:
            logger.warning(f"[{i}] ⚠️ audio yuklab bo'lmadi: {title}")


# ─── Ichki yordamchilar ───────────────────────────────────────────────────────

async def _download_single(
    url: str, opts: dict, chat_id: int, ext: str
) -> Optional[str]:
    """yt-dlp bilan bitta faylni yuklab, yo'lini qaytaradi."""
    loop = asyncio.get_event_loop()
    before = _snapshot(chat_id)

    def _dl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    try:
        await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(f"Yuklashda xato ({url}): {e}")
        return None

    after = _snapshot(chat_id)
    new = after - before

    # Kutilgan kengaytma
    for f in new:
        if Path(f).suffix == ext:
            return f
    # Fallback: ixtiyoriy yangi fayl
    return next(iter(new), None)


def _snapshot(chat_id: int) -> set[str]:
    """Yuklamalar papkasidagi foydalanuvchi fayllarini ro'yxatga olish."""
    return {
        str(p)
        for p in Path(DOWNLOAD_DIR).glob(f"{chat_id}_*")
        if p.is_file()
    }


async def _get_playlist_entries(url: str) -> tuple[list[dict], int]:
    """Playlist entry'larini olish. (entries, total)"""
    info = await get_video_info(url)
    if not info:
        return [], 0
    entries = info.get("entries") or []
    return entries, len(entries)
