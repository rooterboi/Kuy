"""Music Bot - kirish nuqtasi."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DB_PATH
from database.db import Database
from handlers import admin, downloader, features, search, settings, shazam, start
from handlers.errors import register_error_handler
from utils import system
from utils.alerts import notify_admins
from utils.logger import get_logger, setup_logging
from utils.middlewares import AccessMiddleware
from utils.webserver import start_web_server

setup_logging()
log = get_logger("bot")

_last_alert: dict[str, float] = {}


async def maintenance_loop(bot: Bot) -> None:
    """Har 10 daqiqada: eski keshni tozalaydi, disk/xotira to'lishini tekshiradi (Auto-Alert)."""
    loop = asyncio.get_running_loop()
    while True:
        await asyncio.sleep(600)
        try:
            system.clean_tmp(older_than_sec=1800)
            total, _used, free = system.disk_info()
            if free / total < 0.10:
                system.clean_tmp(0)
                await _throttled_alert(bot, loop, "disk", "💾 <b>Disk to‘lib qolmoqda!</b> Kesh avtomatik tozalandi.")
            mem = system.memory_info()
            if mem and mem[1] / mem[0] > 0.90:
                await _throttled_alert(bot, loop, "mem", "🧠 <b>Xotira 90% dan oshdi!</b> Botni qayta yuklash tavsiya etiladi.")
        except Exception:
            log.exception("maintenance_loop xatosi")


async def _throttled_alert(bot: Bot, loop, key: str, text: str) -> None:
    now = loop.time()
    if now - _last_alert.get(key, -1e9) > 3600:  # bir turdagi ogohlantirish soatiga 1 marta
        _last_alert[key] = now
        await notify_admins(bot, text)


async def main() -> None:
    db = Database(DB_PATH)
    await db.connect()

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db

    # Middleware (ban, til, majburiy obuna)
    access = AccessMiddleware(db)
    dp.message.outer_middleware(access)
    dp.callback_query.outer_middleware(access)

    # Routerlar tartibi muhim: umumiy matn qidiruvi (search) eng oxirida
    dp.include_routers(
        admin.router, start.router, settings.router, features.router,
        shazam.router, downloader.router, search.router,
    )
    register_error_handler(dp, bot, db)

    runner = await start_web_server()  # Render health-check
    # Eski (to'planib qolgan) update'larni tashlaymiz: restartdan keyin qayta ishlanib ketmasligi uchun
    await bot.delete_webhook(drop_pending_updates=True)
    maintenance = asyncio.create_task(maintenance_loop(bot))

    me = await bot.me()
    log.info("Bot ishga tushdi: @%s | yt-dlp %s", me.username, system.get_ytdlp_version())
    await notify_admins(bot, f"✅ <b>Bot ishga tushdi</b> (@{me.username})\nyt-dlp: <code>{system.get_ytdlp_version()}</code>")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        maintenance.cancel()
        await runner.cleanup()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot to'xtatildi")
