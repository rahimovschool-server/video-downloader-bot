import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
)

from services.detector import detect_url, is_youtube, is_instagram, UrlType
from services.yt_service import (
    get_video_info,
    download_video,
    download_audio,
    playlist_download_videos,
    playlist_download_audio,
)
from services.ig_service import download_ig_video, download_ig_audio, download_ig_images
from services.cache import get_cached, save_cache
from services.uploader import upload_video, upload_audio, upload_photo, upload_document
from keyboards.inline import main_menu_kb, video_quality_kb, audio_quality_kb, cancel_kb
from utils.cleaner import clean_user_files, get_file_size_mb
from config import PLAYLIST_MAX_ITEMS

logger = logging.getLogger(__name__)
router = Router()

# ─── Sifat nomlari ───────────────────────────────────────────────────────────
VIDEO_LABELS = {
    "2160": "4K (2160p)", "1080": "Full HD (1080p)",
    "720": "HD (720p)", "480": "SD (480p)", "360": "Low (360p)",
}
AUDIO_LABELS = {
    "320": "320 kbps (Yuqori)",
    "192": "192 kbps (O'rta)",
    "128": "128 kbps (Standart)",
}


# ─── URL qabul qilish ────────────────────────────────────────────────────────

@router.message(F.text)
async def handle_url(message: Message) -> None:
    text = message.text or ""
    url, url_type = detect_url(text)

    if not url or url_type == UrlType.UNKNOWN:
        await message.answer(
            "❌ <b>Noto'g'ri havola!</b>\n\n"
            "YouTube yoki Instagram havolasini yuboring.\n"
            "Misol: <code>https://youtube.com/watch?v=...</code>",
            parse_mode="HTML"
        )
        return

    status = await message.answer("🔍 Havola tekshirilmoqda...")

    try:
        if is_youtube(url_type):
            info = await get_video_info(url)
            if not info:
                await status.edit_text("⚠️ Video topilmadi. Havolani tekshiring.")
                return

            is_playlist = bool(info.get("entries"))
            title = info.get("title", "Video")
            uploader = info.get("uploader", "Noma'lum")
            count = len(info.get("entries", [])) if is_playlist else 1
            duration = info.get("duration", 0) or 0
            views = info.get("view_count", 0) or 0

            if is_playlist:
                limit_txt = (
                    f"Cheksiz" if PLAYLIST_MAX_ITEMS == 0
                    else str(PLAYLIST_MAX_ITEMS)
                )
                caption = (
                    f"📋 <b>Playlist:</b> {title[:50]}\n"
                    f"👤 Kanal: {uploader}\n"
                    f"🎞 Videolar: <b>{count} ta</b>\n"
                    f"⚙️ Limit: {limit_txt}\n\n"
                    f"⬇️ Nimani yuklamoqchisiz?"
                )
            else:
                m, s = divmod(int(duration), 60)
                caption = (
                    f"📹 <b>{title[:60]}</b>\n"
                    f"👤 {uploader}\n"
                    f"⏱ {m}:{s:02d}  |  👁 {views:,}\n\n"
                    f"⬇️ Nimani yuklamoqchisiz?"
                )

            thumb = info.get("thumbnail", "")
            await status.delete()
            if thumb:
                try:
                    await message.answer_photo(
                        photo=thumb, caption=caption,
                        parse_mode="HTML",
                        reply_markup=main_menu_kb(url, url_type),
                    )
                    return
                except Exception:
                    pass
            await message.answer(caption, parse_mode="HTML",
                                 reply_markup=main_menu_kb(url, url_type))

        elif is_instagram(url_type):
            type_name = {
                UrlType.INSTAGRAM_POST: "Instagram Post",
                UrlType.INSTAGRAM_REEL: "Instagram Reel",
                UrlType.INSTAGRAM_STORY: "Instagram Story",
            }.get(url_type, "Instagram")
            await status.delete()
            await message.answer(
                f"📸 <b>{type_name}</b>\n\n⬇️ Nimani yuklamoqchisiz?",
                parse_mode="HTML",
                reply_markup=main_menu_kb(url, url_type),
            )

    except Exception as e:
        logger.error(f"handle_url xato: {e}")
        await status.edit_text("❌ Xato yuz berdi. Qayta urinib ko'ring.")


# ─── Tugma callbacklari ──────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer("❌ Bekor qilindi")


@router.callback_query(F.data.startswith("back|"))
async def cb_back(callback: CallbackQuery) -> None:
    url = callback.data.split("|", 1)[1]
    _, url_type = detect_url(url)
    await callback.message.edit_reply_markup(reply_markup=main_menu_kb(url, url_type))
    await callback.answer()


@router.callback_query(F.data.startswith("select_video|"))
async def cb_select_video(callback: CallbackQuery) -> None:
    url = callback.data.split("|", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=video_quality_kb(url))
    await callback.answer("🎬 Sifatni tanlang")


@router.callback_query(F.data.startswith("select_audio|"))
async def cb_select_audio(callback: CallbackQuery) -> None:
    url = callback.data.split("|", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=audio_quality_kb(url))
    await callback.answer("🎵 Sifatni tanlang")


# ─── Rasm yuklash ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("select_image|"))
async def cb_select_image(callback: CallbackQuery) -> None:
    url = callback.data.split("|", 1)[1]
    chat_id = callback.from_user.id

    await callback.message.edit_text(
        "🖼️ <b>Rasmlar yuklanmoqda...</b>\n⏳ Iltimos kuting...",
        parse_mode="HTML"
    )
    await callback.answer()

    files = await download_ig_images(url, chat_id)
    if not files:
        await callback.message.edit_text("❌ Rasmlarni yuklab bo'lmadi!")
        return

    img_files = [f for f in files if Path(f).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    vid_files = [f for f in files if Path(f).suffix.lower() in (".mp4", ".webm")]

    sent = 0
    try:
        # Rasmlar
        if img_files:
            if len(img_files) == 1:
                file_id = await _upload_and_cache(img_files[0], url, "orig", "image")
                await callback.message.answer_photo(photo=file_id, caption="🖼️ Rasm yuborildi!")
                sent += 1
            else:
                media = []
                for fp in img_files[:10]:
                    fid = await _upload_and_cache(fp, url, f"img_{img_files.index(fp)}", "image")
                    media.append(InputMediaPhoto(media=fid))
                await callback.message.answer_media_group(media=media)
                sent += len(media)

        # Videolar
        for fp in vid_files[:5]:
            file_id = await _upload_and_cache(fp, url, "igvid", "video")
            await callback.message.answer_video(video=file_id, caption="🎬 Video yuborildi!")
            sent += 1

        await callback.message.edit_text(f"✅ <b>{sent} ta fayl yuborildi!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Rasm yuborishda xato: {e}")
        await callback.message.edit_text("❌ Faylni yuborishda xato.")
    finally:
        clean_user_files(chat_id)


# ─── Video yuklash ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("dl_video|"))
async def cb_download_video(callback: CallbackQuery) -> None:
    _, quality, url = callback.data.split("|", 2)
    chat_id = callback.from_user.id
    label = VIDEO_LABELS.get(quality, f"{quality}p")
    _, url_type = detect_url(url)

    # ─ Cache tekshirish ─
    cached = await get_cached(url, quality, "video")
    if cached:
        await callback.answer("⚡ Keshdan yuborilmoqda!")
        await callback.message.edit_text("⚡ <b>Keshdan yuborilmoqda...</b>", parse_mode="HTML")
        await callback.message.answer_video(
            video=cached,
            caption=f"✅ <b>Video (kesh)</b>\n📊 {label}",
            parse_mode="HTML",
        )
        await callback.message.delete()
        return

    # ─ Yangi yuklash ─
    await callback.message.edit_text(
        f"⬇️ <b>Yuklanmoqda...</b>\n📊 Sifat: <b>{label}</b>\n⏳ Kuting...",
        parse_mode="HTML"
    )
    await callback.answer(f"📥 {label} yuklanmoqda...")

    is_playlist_url = url_type == UrlType.YOUTUBE_PLAYLIST

    try:
        if is_playlist_url:
            await _handle_playlist_video(callback, url, quality, chat_id, label)
        else:
            fp = await (
                download_video(url, quality, chat_id)
                if is_youtube(url_type)
                else download_ig_video(url, quality, chat_id)
            )
            if not fp or not Path(fp).exists():
                await callback.message.edit_text(
                    "❌ Video topilmadi! Boshqa sifat tanlang.",
                    reply_markup=video_quality_kb(url)
                )
                return

            size_mb = get_file_size_mb(fp)
            await callback.message.edit_text(
                f"📤 <b>Telegram kanaliga yuklanmoqda...</b>\n📦 {size_mb:.1f} MB",
                parse_mode="HTML"
            )

            file_id = await upload_video(fp, caption=f"{label}")
            await save_cache(url, quality, "video", file_id, size_mb)

            await callback.message.answer_video(
                video=file_id,
                caption=f"✅ <b>Video yuborildi!</b>\n📊 {label} | 📦 {size_mb:.1f} MB",
                parse_mode="HTML",
                supports_streaming=True,
            )
            await callback.message.delete()

    except Exception as e:
        logger.error(f"Video yuborishda xato: {e}")
        await callback.message.edit_text("❌ Xato yuz berdi.", reply_markup=cancel_kb())
    finally:
        clean_user_files(chat_id)


async def _handle_playlist_video(
    callback: CallbackQuery, url: str, quality: str, chat_id: int, label: str
) -> None:
    """Playlist videolarini ketma-ket yuklab yuborish."""
    count = 0
    status_msg = callback.message

    async for fp, title, i, total in playlist_download_videos(url, quality, chat_id):
        try:
            await status_msg.edit_text(
                f"📋 <b>Playlist [{i}/{total}]</b>\n"
                f"🎬 {title[:50]}\n"
                f"📤 Yuklanmoqda...",
                parse_mode="HTML"
            )
            size_mb = get_file_size_mb(fp)
            cached = await get_cached(fp, quality, "video")  # URL o'rniga video URL
            if not cached:
                file_id = await upload_video(fp, caption=f"{i}/{total} | {title[:60]}")
                await save_cache(url + f"#item{i}", quality, "video", file_id, size_mb)
            else:
                file_id = cached

            await callback.message.answer_video(
                video=file_id,
                caption=f"🎬 <b>{i}/{total}</b> | {title[:60]}\n📊 {label} | 📦 {size_mb:.1f} MB",
                parse_mode="HTML",
                supports_streaming=True,
            )
            count += 1
        except Exception as e:
            logger.error(f"Playlist video [{i}] xato: {e}")
        finally:
            clean_user_files(chat_id)

    await status_msg.edit_text(
        f"✅ <b>Playlist yakunlandi!</b>\n📊 {count} ta video yuborildi.",
        parse_mode="HTML"
    )


# ─── Audio yuklash ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("dl_audio|"))
async def cb_download_audio(callback: CallbackQuery) -> None:
    _, quality, url = callback.data.split("|", 2)
    chat_id = callback.from_user.id
    label = AUDIO_LABELS.get(quality, f"{quality} kbps")
    _, url_type = detect_url(url)

    # ─ Cache tekshirish ─
    cached = await get_cached(url, quality, "audio")
    if cached:
        await callback.answer("⚡ Keshdan yuborilmoqda!")
        await callback.message.edit_text("⚡ <b>Keshdan yuborilmoqda...</b>", parse_mode="HTML")
        await callback.message.answer_audio(
            audio=cached,
            caption=f"✅ <b>Audio (kesh)</b>\n🎵 {label}",
            parse_mode="HTML",
        )
        await callback.message.delete()
        return

    await callback.message.edit_text(
        f"🎵 <b>Yuklanmoqda...</b>\n📊 Sifat: <b>{label}</b>\n⏳ Kuting...",
        parse_mode="HTML"
    )
    await callback.answer(f"🎵 {label} yuklanmoqda...")

    is_playlist_url = url_type == UrlType.YOUTUBE_PLAYLIST

    try:
        if is_playlist_url:
            await _handle_playlist_audio(callback, url, quality, chat_id, label)
        else:
            fp = await (
                download_audio(url, quality, chat_id)
                if is_youtube(url_type)
                else download_ig_audio(url, quality, chat_id)
            )
            if not fp or not Path(fp).exists():
                await callback.message.edit_text(
                    "❌ Audio yuklab bo'lmadi!", reply_markup=audio_quality_kb(url)
                )
                return

            size_mb = get_file_size_mb(fp)
            await callback.message.edit_text(
                f"📤 <b>Telegram kanaliga yuklanmoqda...</b>\n📦 {size_mb:.1f} MB",
                parse_mode="HTML"
            )

            file_id = await upload_audio(fp, caption=label)
            await save_cache(url, quality, "audio", file_id, size_mb)

            await callback.message.answer_audio(
                audio=file_id,
                caption=f"✅ <b>Audio yuborildi!</b>\n🎵 {label} | 📦 {size_mb:.1f} MB",
                parse_mode="HTML",
            )
            await callback.message.delete()

    except Exception as e:
        logger.error(f"Audio yuborishda xato: {e}")
        await callback.message.edit_text("❌ Xato yuz berdi.", reply_markup=cancel_kb())
    finally:
        clean_user_files(chat_id)


async def _handle_playlist_audio(
    callback: CallbackQuery, url: str, quality: str, chat_id: int, label: str
) -> None:
    """Playlist audiolarini ketma-ket yuklab yuborish."""
    count = 0
    status_msg = callback.message

    async for fp, title, i, total in playlist_download_audio(url, quality, chat_id):
        try:
            await status_msg.edit_text(
                f"📋 <b>Playlist [{i}/{total}]</b>\n"
                f"🎵 {title[:50]}\n"
                f"📤 Yuklanmoqda...",
                parse_mode="HTML"
            )
            size_mb = get_file_size_mb(fp)
            file_id = await upload_audio(fp, caption=f"{i}/{total} | {title[:60]}")
            await save_cache(url + f"#audio{i}", quality, "audio", file_id, size_mb)

            await callback.message.answer_audio(
                audio=file_id,
                caption=f"🎵 <b>{i}/{total}</b> | {title[:60]}\n🎶 {label} | 📦 {size_mb:.1f} MB",
                parse_mode="HTML",
                title=title[:64],
            )
            count += 1
        except Exception as e:
            logger.error(f"Playlist audio [{i}] xato: {e}")
        finally:
            clean_user_files(chat_id)

    await status_msg.edit_text(
        f"✅ <b>Playlist yakunlandi!</b>\n🎵 {count} ta audio yuborildi.",
        parse_mode="HTML"
    )


# ─── Yordamchi ───────────────────────────────────────────────────────────────

async def _upload_and_cache(
    filepath: str, url: str, quality: str, media_type: str
) -> str:
    """Faylni yuklaydi va keshga saqlaydi, file_id qaytaradi."""
    cached = await get_cached(url, quality, media_type)
    if cached:
        return cached

    size_mb = get_file_size_mb(filepath)
    ext = Path(filepath).suffix.lower()

    if media_type == "image" or ext in (".jpg", ".jpeg", ".png", ".webp"):
        file_id = await upload_photo(filepath)
    elif media_type == "audio" or ext == ".mp3":
        file_id = await upload_audio(filepath)
    elif media_type == "video" or ext in (".mp4", ".webm"):
        file_id = await upload_video(filepath)
    else:
        file_id = await upload_document(filepath)

    await save_cache(url, quality, media_type, file_id, size_mb)
    return file_id
