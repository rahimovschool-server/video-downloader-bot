import os
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN, DOWNLOAD_DIR
from handlers import start, downloader
from utils.cleaner import clean_all_old_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my-secret-token-12345"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(downloader.router)
    return dp

async def periodic_cleanup():
    while True:
        await asyncio.sleep(1800)
        removed = clean_all_old_files(max_age_hours=1)
        if removed > 0:
            logger.info(f"🗑️ {removed} ta eski fayl o'chirildi")

async def on_startup(bot: Bot) -> None:
    if RAILWAY_DOMAIN:
        wh = f"https://{RAILWAY_DOMAIN}{WEBHOOK_PATH}"
        await bot.set_webhook(url=wh, secret_token=WEBHOOK_SECRET, drop_pending_updates=True)
    logger.info(f"🤖 Bot ishga tushdi (Oddiy rejim)")

async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logger.info("🛑 Bot to'xtatildi")

def run_webhook() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    app = web.Application()
    SimpleRequestHandler(dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)

async def run_polling() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()
    await on_startup(bot)
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await on_shutdown(bot)
        await bot.session.close()

if __name__ == "__main__":
    if RAILWAY_DOMAIN:
        run_webhook()
    else:
        asyncio.run(run_polling())
