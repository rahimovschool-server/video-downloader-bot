"""
Bot ishga tushishdan oldin barcha kutubxonalar
va muhit o'zgaruvchilarini tekshirish skripti.

Ishlatish:
    python check.py
"""
import sys
import os
import importlib

print("=" * 55)
print("  🔍 Media Downloader Bot — Tekshiruv")
print("=" * 55)

errors = []
warnings = []

# ─── Python versiyasi ───────────────────────────────────────
py = sys.version_info
print(f"\n🐍 Python: {py.major}.{py.minor}.{py.micro}", end="")
if py.major < 3 or (py.major == 3 and py.minor < 10):
    errors.append("Python 3.10+ talab qilinadi!")
    print(" ❌")
else:
    print(" ✅")

# ─── Kutubxonalar ──────────────────────────────────────────
packages = [
    ("aiogram",     "aiogram"),
    ("yt_dlp",      "yt-dlp"),
    ("pyrogram",    "pyrogram"),
    ("aiosqlite",   "aiosqlite"),
    ("aiohttp",     "aiohttp"),
    ("dotenv",      "python-dotenv"),
    ("aiofiles",    "aiofiles"),
    ("instaloader", "instaloader"),
]

print("\n📦 Kutubxonalar:")
for mod, pkg in packages:
    try:
        importlib.import_module(mod)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg}  ← pip install {pkg}")
        errors.append(f"{pkg} o'rnatilmagan")

# ─── FFmpeg ────────────────────────────────────────────────
print("\n🎞️  FFmpeg:")
ffmpeg_ok = os.system("ffmpeg -version >nul 2>&1") == 0
if not ffmpeg_ok:
    ffmpeg_ok = os.system("ffmpeg -version >/dev/null 2>&1") == 0
if ffmpeg_ok:
    print("   ✅ FFmpeg topildi")
else:
    print("   ❌ FFmpeg topilmadi — audio/video konvertatsiya ishlamaydi!")
    errors.append("FFmpeg o'rnatilmagan")

# ─── .env fayl ─────────────────────────────────────────────
print("\n⚙️  Muhit o'zgaruvchilari:")
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

required_vars = [
    ("BOT_TOKEN",          "BotFather tokeni"),
    ("API_ID",             "my.telegram.org"),
    ("API_HASH",           "my.telegram.org"),
    ("STRING_SESSION",     "python utils/session_gen.py"),
    ("STORAGE_CHANNEL_ID", "Yopiq kanal ID"),
]

for var, hint in required_vars:
    val = os.getenv(var, "")
    if val and val not in ("0", ""):
        print(f"   ✅ {var}")
    else:
        print(f"   ❌ {var}  ← {hint}")
        errors.append(f"{var} kiritilmagan")

optional_vars = [
    ("INSTAGRAM_USERNAME", "Instagram login (ixtiyoriy)"),
    ("INSTAGRAM_PASSWORD", "Instagram parol (ixtiyoriy)"),
]
for var, hint in optional_vars:
    val = os.getenv(var, "")
    if val:
        print(f"   ✅ {var}")
    else:
        print(f"   ⚠️  {var}  ← {hint}")
        warnings.append(f"{var} kiritilmagan (ixtiyoriy)")

# ─── Natija ────────────────────────────────────────────────
print("\n" + "=" * 55)
if errors:
    print(f"❌ {len(errors)} ta xato topildi:\n")
    for e in errors:
        print(f"   • {e}")
    print("\n🛠️  Xatolarni to'g'rilab qayta ishga tushiring.")
else:
    print("✅ Hammasi joyida! Bot ishga tushirishga tayyor.")
    print("\n   python bot.py")

if warnings:
    print(f"\n⚠️  {len(warnings)} ta ogohlantirish:")
    for w in warnings:
        print(f"   • {w}")

print("=" * 55)
