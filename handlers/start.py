from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()

WELCOME_TEXT = """
🤖 <b>Media Downloader Bot</b>ga xush kelibsiz!

📥 <b>Nima yuklay olaman?</b>
━━━━━━━━━━━━━━━━━━
🎬 <b>YouTube:</b>
  • Video (4K / 1080p / 720p / 480p / 360p)
  • Audio MP3 (320 / 192 / 128 kbps)
  • Shorts videolari
  • Playlist (birinchi 10 ta)

📸 <b>Instagram:</b>
  • Video va Reels
  • Post rasmlari
  • Audio ajratib olish

━━━━━━━━━━━━━━━━━━
📌 <b>Qanday ishlatiladi?</b>
YouTube yoki Instagram havolasini yuboring — men sifatni tanlashingizga yordam beraman!

⚠️ <b>Eslatma:</b> Telegram 50 MB gacha fayl qabul qiladi.
"""

HELP_TEXT = """
📖 <b>Yordam</b>

🔗 <b>Qo'llab-quvvatlanadigan havolalar:</b>
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/shorts/...
• instagram.com/p/...
• instagram.com/reel/...

🛠 <b>Buyruqlar:</b>
/start — Botni ishga tushirish
/help — Bu yordam xabarini ko'rish

❓ <b>Muammo bo'lsa:</b>
• FFmpeg o'rnatilganligini tekshiring
• Havola to'g'ri ekanligini tekshiring
• Instagram private post bo'lmasin
"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
