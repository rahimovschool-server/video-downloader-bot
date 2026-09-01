import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")
