import os
import asyncio
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from services.detector import detect_url_type
from services.yt_service import download_video, download_audio
from services.ig_service import download_ig_video, download_ig_audio, download_ig_images
from keyboards.inline import video_quality_kb, audio_quality_kb
from utils.cleaner import get_file_size_mb
import shutil

router = Router()

@router.message(F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    url_type = detect_url_type(url)
    if not url_type:
        await message.answer("❌ Noto'g'ri yoki qo'llab-quvvatlanmaydigan havola.")
        return
    await message.answer("🎬 Nimani yuklab olmoqchisiz?", reply_markup=video_quality_kb(url))

@router.callback_query(F.data.startswith("vid_") | F.data.startswith("aud_"))
async def handle_quality_selection(call: CallbackQuery):
    await call.message.edit_text("⏳ Yuklanmoqda, kuting...")
    parts = call.data.split("|")
    action, quality = parts[0].split("_")
    url = parts[1]
    url_type = detect_url_type(url)
    chat_id = call.message.chat.id
    
    filepath = None
    try:
        if url_type == "youtube":
            if action == "vid":
                filepath = await download_video(url, quality, chat_id)
            else:
                filepath = await download_audio(url, quality, chat_id)
        elif url_type == "instagram":
            if action == "vid":
                filepath = await download_ig_video(url, chat_id)
            else:
                filepath = await download_ig_audio(url, chat_id)

        if not filepath or not os.path.exists(filepath):
            await call.message.edit_text("⚠️ Faylni yuklab bo'lmadi.")
            return

        size = get_file_size_mb(filepath)
        if size > 49.5:
            await call.message.edit_text("❌ Fayl hajmi 50MB dan katta. Telegram botlari faqat 50MB gacha yubora oladi.")
            os.remove(filepath)
            return

        inp_file = FSInputFile(filepath)
        if action == "vid":
            await call.message.answer_video(video=inp_file, caption="✅ @tezviddownbot orqali yuklandi")
        else:
            await call.message.answer_audio(audio=inp_file, caption="✅ @tezviddownbot orqali yuklandi")
            
        await call.message.delete()
        
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi: {e}")
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
