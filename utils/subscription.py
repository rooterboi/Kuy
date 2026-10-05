"""Majburiy kanalga obuna tekshiruvi."""
import time

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_IDS
from database.db import Database
from utils.i18n import t
from utils.keyboards import subscribe_kb
from utils.logger import get_logger

log = get_logger(__name__)

_verified: dict[int, float] = {}  # user_id -> tekshirilgan vaqt (API so'rovlarini kamaytirish uchun kesh)
CACHE_TTL = 90


def mark_verified(user_id: int) -> None:
    _verified[user_id] = time.monotonic()


async def get_unsubscribed(bot: Bot, user_id: int, channels: list[dict]) -> list[dict]:
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
                missing.append(ch)
        except TelegramAPIError as exc:
            # Bot kanalda admin emas / kanal o'chirilgan: foydalanuvchini qamab qo'ymaymiz
            log.warning("Obuna tekshiruvi xatosi (%s): %s", ch["chat_id"], exc)
    return missing


async def check_and_prompt(bot: Bot, db: Database, user_id: int, lang: str) -> bool:
    """True — foydalanuvchi ruxsat etilgan. False — obuna so'rovi yuborildi."""
    if user_id in ADMIN_IDS:
        return True
    if time.monotonic() - _verified.get(user_id, 0) < CACHE_TTL:
        return True
    channels = await db.list_channels()
    if not channels:
        return True
    missing = await get_unsubscribed(bot, user_id, channels)
    if not missing:
        mark_verified(user_id)
        return True
    await bot.send_message(user_id, t(lang, "must_join"), reply_markup=subscribe_kb(lang, missing))
    return False
