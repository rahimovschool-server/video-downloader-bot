import logging
import os
from pathlib import Path
from typing import Optional, AsyncGenerator

import yt_dlp
import asyncio

from config import DOWNLOAD_DIR, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = logging.getLogger(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_IG_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 60,
    "retries": 5,
}


def _ig_opts(extra: dict = {}) -> dict:
    opts = {**_IG_BASE_OPTS, **extra}
    if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
        opts["username"] = INSTAGRAM_USERNAME
        opts["password"] = INSTAGRAM_PASSWORD
    return opts


# ─── Instagram Video / Reel ───────────────────────────────────────────────────

async def download_ig_video(url: str, quality: str, chat_id: int) -> Optional[str]:
    """Instagram video/reel yuklash. Limit yo'q."""
    fmt = (
        f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={quality}]+bestaudio/"
        f"best[height<={quality}]/best"
    )
    opts = _ig_opts({
        "format": fmt,
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{chat_id}_ig_%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
    })

    return await _run(url, opts, chat_id, prefix="ig_", ext=".mp4")


async def download_ig_audio(url: str, quality: str, chat_id: int) -> Optional[str]:
    """Instagram videodан audio ajratib olish (MP3)."""
    opts = _ig_opts({
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{chat_id}_ig_%(id)s.%(ext)s"),
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality},
        ],
    })
    return await _run(url, opts, chat_id, prefix="ig_", ext=".mp3")


# ─── Instagram Rasmlar ────────────────────────────────────────────────────────

async def download_ig_images(url: str, chat_id: int) -> list[str]:
    """
    Instagram post rasmlari va videolarini yuklash.
    Ko'p media (carousel) bo'lsa hammasini yuklab beradi.
    """
    opts = _ig_opts({
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{chat_id}_igimg_%(autonumber)04d.%(ext)s"),
        "format": "best",
        "writesubtitles": False,
        "writethumbnail": False,
    })

    loop = asyncio.get_event_loop()
    before = _snapshot_any(chat_id, "igimg_")

    def _dl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    try:
        await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(f"Instagram rasm yuklab bo'lmadi: {e}")
        # Instaloader bilan urinib ko'ramiz
        return await _instaloader_fallback(url, chat_id)

    after = _snapshot_any(chat_id, "igimg_")
    new = list(after - before)

    if not new:
        return await _instaloader_fallback(url, chat_id)

    return new


async def _instaloader_fallback(url: str, chat_id: int) -> list[str]:
    """Instaloader bilan Instagram rasmlari yuklash (zaxira)."""
    try:
        import instaloader
        import re

        match = re.search(r"/(?:p|reel|tv)/([\w-]+)", url)
        if not match:
            return []

        shortcode = match.group(1)
        target_dir = os.path.join(DOWNLOAD_DIR, f"{chat_id}_insta")
        os.makedirs(target_dir, exist_ok=True)

        loop = asyncio.get_event_loop()

        def _dl():
            L = instaloader.Instaloader(
                dirname_pattern=target_dir,
                filename_pattern=f"{chat_id}_{{shortcode}}_{{mediaid}}",
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                quiet=True,
            )
            if INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                except Exception:
                    pass
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target=target_dir)
            return [
                str(f) for f in Path(target_dir).glob("*")
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4")
            ]

        return await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(f"Instaloader xatosi: {e}")
        return []


# ─── Ichki yordamchilar ───────────────────────────────────────────────────────

async def _run(url: str, opts: dict, chat_id: int, prefix: str, ext: str) -> Optional[str]:
    loop = asyncio.get_event_loop()
    before = _snapshot_any(chat_id, prefix)

    def _dl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    try:
        await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(f"Instagram yuklash xatosi: {e}")
        return None

    after = _snapshot_any(chat_id, prefix)
    new = after - before

    for f in new:
        if Path(f).suffix == ext:
            return f
    return next(iter(new), None)


def _snapshot_any(chat_id: int, prefix: str) -> set[str]:
    return {
        str(p) for p in Path(DOWNLOAD_DIR).glob(f"{chat_id}_{prefix}*")
        if p.is_file()
    }
