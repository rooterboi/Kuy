"""Global xatolik ushlagich: log + adminga Auto-Alert."""
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ErrorEvent

from database.db import Database
from utils.alerts import report_error
from utils.i18n import t


def register_error_handler(dp: Dispatcher, bot: Bot, db: Database) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        exc = event.exception
        # Zararsiz xatolar: ogohlantirish yubormaymiz
        if isinstance(exc, TelegramForbiddenError):
            return True
        if isinstance(exc, TelegramBadRequest) and any(
            s in str(exc).lower() for s in ("message is not modified", "query is too old", "message to delete not found")
        ):
            return True

        update = event.update
        source = update.message or update.callback_query
        user = source.from_user if source else None
        code = await report_error(bot, exc, user=user, where="global handler")

        try:
            if user:
                row = await db.get_user(user.id)
                lang = (row or {}).get("lang") or "uz"
                await bot.send_message(user.id, t(lang, "error", code=code))
        except Exception:
            pass
        return True
