from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.detector import UrlType


# ─────────────────── Video sifat tugmalari ───────────────────

VIDEO_QUALITIES = [
    ("🔥 4K (2160p)", "2160"),
    ("🏆 Full HD (1080p)", "1080"),
    ("✨ HD (720p)", "720"),
    ("📱 SD (480p)", "480"),
    ("💾 Low (360p)", "360"),
]

AUDIO_QUALITIES = [
    ("🎵 320 kbps (Yuqori)", "320"),
    ("🎶 192 kbps (O'rta)", "192"),
    ("🔊 128 kbps (Standart)", "128"),
]


def main_menu_kb(url: str, url_type: UrlType) -> InlineKeyboardMarkup:
    """Asosiy menyu: Video / Audio / Rasm tanlash."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🎬 Video yuklash",
        callback_data=f"select_video|{url}"
    )
    builder.button(
        text="🎵 Audio (MP3) yuklash",
        callback_data=f"select_audio|{url}"
    )

    if url_type in (UrlType.INSTAGRAM_POST, UrlType.INSTAGRAM_REEL):
        builder.button(
            text="🖼️ Rasm(lar) yuklash",
            callback_data=f"select_image|{url}"
        )

    builder.button(
        text="❌ Bekor qilish",
        callback_data="cancel"
    )

    builder.adjust(2, 1, 1)
    return builder.as_markup()


def video_quality_kb(msg_id: int) -> InlineKeyboardMarkup:
    """Video sifat tanlash tugmalari."""
    builder = InlineKeyboardBuilder()

    for label, quality in VIDEO_QUALITIES:
        builder.button(
            text=label,
            callback_data=f"vid_{quality}_{msg_id}"
        )

    builder.adjust(1)
    return builder.as_markup()


def audio_quality_kb(msg_id: int) -> InlineKeyboardMarkup:
    """Audio sifat tanlash tugmalari."""
    builder = InlineKeyboardBuilder()

    for label, quality in AUDIO_QUALITIES:
        builder.button(
            text=label,
            callback_data=f"aud_{quality}_{msg_id}"
        )

    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    return builder.as_markup()
