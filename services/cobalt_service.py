import os
import asyncio
import logging
import aiohttp
from pathlib import Path
from config import DOWNLOAD_DIR

logger = logging.getLogger(__name__)

COBALT_API = "https://api.cobalt.tools/"

async def cobalt_download(url: str, is_audio: bool, quality: str, chat_id: int) -> str | None:
    """Cobalt API orqali media url ini oladi va faylga saqlaydi."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # Sifat moslashtirish (cobalt qabul qiladigan formatlar)
    video_quality = quality
    if quality not in ["360", "480", "720", "1080", "1440", "2160", "max"]:
        video_quality = "720"

    payload = {
        "url": url,
        "videoQuality": video_quality,
        "filenamePattern": "classic"
    }
    
    if is_audio:
        payload["isAudioOnly"] = True
        payload["audioFormat"] = "mp3"
        ext = ".mp3"
    else:
        ext = ".mp4"

    try:
        async with aiohttp.ClientSession() as session:
            # 1. API ga so'rov
            async with session.post(COBALT_API, json=payload, headers=headers, timeout=30) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Cobalt API xatosi: {resp.status} - {text}")
                    return None
                
                data = await resp.json()
                
            status = data.get("status")
            download_url = data.get("url")
            
            if status == "error":
                logger.error(f"Cobalt xatosi: {data.get('text')}")
                return None
                
            if not download_url:
                logger.error(f"Cobalt javobida URL topilmadi: {data}")
                return None

            # 2. Faylni yuklab olish
            file_path = os.path.join(DOWNLOAD_DIR, f"{chat_id}_cobalt_{video_quality}{ext}")
            
            async with session.get(download_url, headers={"User-Agent": headers["User-Agent"]}, timeout=300) as dl_resp:
                if dl_resp.status != 200:
                    logger.error(f"Faylni tortishda xato: {dl_resp.status}")
                    return None
                    
                with open(file_path, "wb") as f:
                    async for chunk in dl_resp.content.iter_chunked(1024 * 1024):
                        f.write(chunk)
                        
            return file_path

    except Exception as e:
        logger.error(f"Cobalt yuklashda xato: {e}")
        return None
