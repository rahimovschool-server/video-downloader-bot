import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
PLAYLIST_MAX_ITEMS: int = int(os.getenv("PLAYLIST_MAX_ITEMS", "0"))
INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
STRING_SESSION: str = os.getenv("STRING_SESSION", "")
STORAGE_CHANNEL_ID: int = int(os.getenv("STORAGE_CHANNEL_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")
