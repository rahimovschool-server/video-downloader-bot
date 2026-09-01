import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot ────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ─── Pyrogram (User account — limit yo'q) ───────────────
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
STRING_SESSION: str = os.getenv("STRING_SESSION", "")

# ─── Storage kanal (fayl saqlanadigan yopiq kanal) ──────
STORAGE_CHANNEL_ID: int = int(os.getenv("STORAGE_CHANNEL_ID", "0"))

# ─── Sozlamalar ─────────────────────────────────────────
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
THROTTLE_RATE: float = float(os.getenv("THROTTLE_RATE", "5"))

# ─── Playlist ───────────────────────────────────────────
PLAYLIST_MAX_ITEMS: int = int(os.getenv("PLAYLIST_MAX_ITEMS", "0"))  # 0 = cheksiz

# ─── Tekshiruv ───────────────────────────────────────────
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")
if API_ID == 0 or not API_HASH:
    raise ValueError("❌ API_ID / API_HASH topilmadi! my.telegram.org dan oling.")
if not STRING_SESSION:
    raise ValueError("❌ STRING_SESSION topilmadi! utils/session_gen.py ni ishga tushiring.")
if STORAGE_CHANNEL_ID == 0:
    raise ValueError("❌ STORAGE_CHANNEL_ID topilmadi! Yopiq kanal ID sini kiriting.")
