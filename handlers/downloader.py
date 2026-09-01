import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from services.detector import detect_url, is_youtube, is_instagram
from services.yt_service import download_video, download_audio
from services.ig_service import download_ig_video, download_ig_audio, download_ig_images
from keyboards.inline import video_quality_kb, audio_quality_kb
from utils.cleaner import get_file_size_mb
from services.cache import get_cached, save_cache
import shutil

router = Router()

URL_CACHE = {}

@router.message(F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    clean_url, url_type = detect_url(url)
    if not clean_url or url_type.value == "unknown":
        await message.answer("❌ Noto'g'ri yoki qo'llab-quvvatlanmaydigan havola.")
        return
        
    URL_CACHE[message.message_id] = clean_url
    await message.answer("🎬 Nimani yuklab olmoqchisiz?", reply_markup=video_quality_kb(message.message_id))

@router.callback_query(F.data.startswith("vid_") | F.data.startswith("aud_"))
async def handle_quality_selection(call: CallbackQuery):
    await call.message.edit_text("⏳ Yuklanmoqda, kuting...")
    parts = call.data.split("_")
    action = parts[0]
    quality = parts[1]
    msg_id = int(parts[2])
    
    clean_url = URL_CACHE.get(msg_id)
    if not clean_url:
        await call.message.edit_text("❌ Havola eskirgan. Iltimos, videoni qaytadan yuboring.")
        return
        
    _, url_type = detect_url(clean_url)
    chat_id = call.message.chat.id
    
    # 1. Keshdan izlaymiz
    cached_file_id = await get_cached(clean_url, quality, url_type.value)
    if cached_file_id:
        try:
            if action == "vid":
                await call.message.answer_video(video=cached_file_id, caption="✅ @tezviddownbot orqali yuklandi ⚡")
            else:
                await call.message.answer_audio(audio=cached_file_id, caption="✅ @tezviddownbot orqali yuklandi ⚡")
            await call.message.delete()
            return
        except Exception:
            pass # Keshdagi fayl o'chib ketgan bo'lsa (yoki yaroqsiz bo'lsa), qayta yuklaymiz.
            
    # 2. Agar keshda bo'lmasa, yuklaymiz
    filepath = None
    try:
        if is_youtube(url_type):
            if action == "vid":
                filepath = await download_video(clean_url, quality, chat_id)
            else:
                filepath = await download_audio(clean_url, quality, chat_id)
        elif is_instagram(url_type):
            if action == "vid":
                filepath = await download_ig_video(clean_url, chat_id)
            else:
                filepath = await download_ig_audio(clean_url, chat_id)

        if not filepath or not os.path.exists(filepath):
            await call.message.edit_text("⚠️ Faylni yuklab bo'lmadi.")
            return

        size = get_file_size_mb(filepath)
        if size > 49.5:
            await call.message.edit_text("❌ Fayl hajmi 50MB dan katta. Telegram botlari faqat 50MB gacha yubora oladi.")
            os.remove(filepath)
            return

        inp_file = FSInputFile(filepath)
        sent_msg = None
        
        if action == "vid":
            sent_msg = await call.message.answer_video(video=inp_file, caption="✅ @tezviddownbot orqali yuklandi")
            file_id = sent_msg.video.file_id
        else:
            sent_msg = await call.message.answer_audio(audio=inp_file, caption="✅ @tezviddownbot orqali yuklandi")
            file_id = sent_msg.audio.file_id
            
        # 3. Muvaffaqiyatli jo'natilsa, keshga saqlaymiz
        if sent_msg and file_id:
            await save_cache(clean_url, quality, url_type.value, file_id, size)
            
        await call.message.delete()
        
    except Exception as e:
        await call.message.edit_text(f"❌ Xatolik yuz berdi: {e}")
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
