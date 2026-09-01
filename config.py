import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
PLAYLIST_MAX_ITEMS: int = int(os.getenv("PLAYLIST_MAX_ITEMS", "0"))
INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")
