"""Auto-Alert: jiddiy xatolarni adminlarga yuborish."""
import traceback
import uuid
from typing import Optional

from aiogram import Bot
from aiogram.types import User

from config import ADMIN_IDS
from utils.helpers import esc
from utils.logger import get_logger

log = get_logger(__name__)

# yt-dlp bloklangan / eskirgan bo'lishi mumkinligini bildiruvchi belgilar
BLOCK_MARKERS = (
    "sign in to confirm", "http error 403", "http error 429", "login required",
    "rate-limit", "unable to extract", "requested format is not available", "cookies",
)


def is_blocked_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(m in text for m in BLOCK_MARKERS)


def new_error_code() -> str:
    return "ERR-" + uuid.uuid4().hex[:6].upper()


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, disable_web_page_preview=True)
        except Exception as exc:  # admin botni start qilmagan bo'lishi mumkin
            log.warning("Adminga (%s) xabar yuborib bo'lmadi: %s", admin_id, exc)


async def report_error(bot: Bot, exc: BaseException, *, user: Optional[User] = None, where: str = "") -> str:
    """Xatoni logga yozadi, adminga yuboradi va foydalanuvchiga ko'rsatiladigan kodni qaytaradi."""
    code = new_error_code()
    user_id = user.id if user else None
    log.error("[%s] %s | user=%s", code, where, user_id, exc_info=exc)

    tb_tail = "".join(traceback.format_exception_only(type(exc), exc))[-700:]
    hint = ""
    if is_blocked_error(exc):
        hint = "\n\n⚠️ <b>yt-dlp bloklangan yoki eskirgan bo‘lishi mumkin.</b> Admin paneldan «🔄 yt-dlp ni Yangilash» ni bosing."

    who = f"<code>{user_id}</code>" + (f" (@{esc(user.username)})" if user and user.username else "")
    await notify_admins(
        bot,
        f"🚨 <b>Xatolik</b> <code>{code}</code>\n"
        f"👤 Foydalanuvchi: {who or '—'}\n"
        f"📍 Joy: {esc(where)[:300]}\n\n"
        f"<pre>{esc(tb_tail)}</pre>{hint}",
    )
    return code
