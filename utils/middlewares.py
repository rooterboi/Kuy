"""Kirish nazorati: ro'yxatga olish, ban, til tanlash va majburiy obuna."""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import ADMIN_IDS, DEFAULT_LANG
from database.db import Database
from utils.i18n import t
from utils.keyboards import language_kb
from utils.subscription import check_and_prompt


class AccessMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db

    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]],
                       event: TelegramObject, data: dict) -> Any:
        user = data.get("event_from_user")
        if user is None or user.is_bot:
            return await handler(event, data)
        if isinstance(event, Message) and event.chat.type != "private":
            return  # bot faqat shaxsiy chatda ishlaydi

        bot = data["bot"]
        await self.db.upsert_user(user.id, user.username, user.full_name)
        row = await self.db.get_user(user.id)
        is_admin = user.id in ADMIN_IDS
        lang = (row or {}).get("lang") or DEFAULT_LANG
        data["lang"] = lang

        # 1) Ban
        if row and row["is_banned"] and not is_admin:
            if isinstance(event, CallbackQuery):
                await event.answer(t(lang, "banned"), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(t(lang, "banned"))
            return

        if is_admin:
            return await handler(event, data)

        # 2) Til hali tanlanmagan: faqat /start va til tugmalariga ruxsat
        if not (row or {}).get("lang"):
            is_start = isinstance(event, Message) and (event.text or "").startswith("/start")
            is_lang_cb = isinstance(event, CallbackQuery) and (event.data or "").startswith("lang:")
            if is_start or is_lang_cb:
                return await handler(event, data)
            if isinstance(event, Message):
                await event.answer(t(DEFAULT_LANG, "choose_lang"), reply_markup=language_kb())
            elif isinstance(event, CallbackQuery):
                await event.answer()
            return

        # 3) Majburiy obuna ("lang:" va "chk_sub" tugmalari o'tkaziladi)
        if isinstance(event, CallbackQuery) and (event.data or "").startswith(("lang:", "chk_sub", "settings:")):
            return await handler(event, data)
        if not await check_and_prompt(bot, self.db, user.id, lang):
            if isinstance(event, CallbackQuery):
                await event.answer()
            return

        return await handler(event, data)
