"""Render uchun minimal health-check server (bepul Web Service port talab qiladi)."""
from aiohttp import web

from config import PORT
from utils.logger import get_logger

log = get_logger(__name__)


async def _health(_request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def start_web_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("Health-check server: port %s", PORT)
    return runner
