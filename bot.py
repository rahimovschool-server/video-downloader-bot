import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN, DOWNLOAD_DIR
from handlers import start, downloader
from services.cache import init_db
from services.uploader import start_client, stop_client
from utils.cleaner import clean_all_old_files

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Railway/Webhook sozlamalari ─────────────────────────────────────────────
RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
WEBHOOK_HOST   = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH   = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "my-secret-token-12345")
PORT = int(os.getenv("PORT", 8080))

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(downloader.router)
    return dp


async def periodic_cleanup():
    """Har 30 daqiqada eski fayllarni tozalash."""
    while True:
        await asyncio.sleep(1800)
        removed = clean_all_old_files(max_age_hours=1)
        if removed > 0:
            logger.info(f"🗑️ {removed} ta eski fayl o'chirildi")


# ─── Ishga tushirishda: baza + Pyrogram ─────────────────────────────────────
async def on_startup(bot: Bot) -> None:
    # 1) SQLite baza
    await init_db()

    # 2) Pyrogram user client
    await start_client()

    # 3) Webhook (agar Railway'da bo'lsa)
    if RAILWAY_DOMAIN or WEBHOOK_HOST:
        wh = _get_webhook_url()
        await bot.set_webhook(url=wh, secret_token=WEBHOOK_SECRET, drop_pending_updates=True)
        logger.info(f"🌐 Webhook: {wh}")

    info = await bot.get_me()
    logger.info(f"🤖 Bot ishga tushdi: @{info.username}")


async def on_shutdown(bot: Bot) -> None:
    await stop_client()
    await bot.delete_webhook()
    logger.info("🛑 Bot to'xtatildi")


def _get_webhook_url() -> str:
    if WEBHOOK_HOST:
        return f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}"
    return f"https://{RAILWAY_DOMAIN}{WEBHOOK_PATH}"


# ─── WEBHOOK rejimi (Railway) ─────────────────────────────────────────────────
def run_webhook() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp  = create_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    handler = SimpleRequestHandler(dp, bot=bot, secret_token=WEBHOOK_SECRET)
    handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    async def _start_cleanup(a): a["ct"] = asyncio.create_task(periodic_cleanup())
    async def _stop_cleanup(a):
        t = a.get("ct")
        if t: t.cancel()

    app.on_startup.append(_start_cleanup)
    app.on_cleanup.append(_stop_cleanup)

    logger.info(f"🚀 Webhook server port={PORT}")
    web.run_app(app, host="0.0.0.0", port=PORT)


# ─── POLLING rejimi (Lokal) ───────────────────────────────────────────────────
async def run_polling() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp  = create_dispatcher()

    await on_startup(bot)
    ct = asyncio.create_task(periodic_cleanup())
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        ct.cancel()
        await on_shutdown(bot)
        await bot.session.close()


# ─── Kirish nuqtasi ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    if RAILWAY_DOMAIN or WEBHOOK_HOST:
        logger.info("📡 Webhook rejimi (Railway)")
        run_webhook()
    else:
        logger.info("🔄 Polling rejimi (Lokal)")
        try:
            asyncio.run(run_polling())
        except KeyboardInterrupt:
            logger.info("👋 To'xtatildi")
