"""Reklama yuborish (Broadcast) - real vaqt progress-bar bilan."""
import asyncio
import time
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.alerts import report_error
from utils.logger import get_logger

log = get_logger(__name__)
BACKGROUND_TASKS: set[asyncio.Task] = set()  # task'larni GC dan saqlash


def parse_buttons(raw: str) -> list[list[str]]:
    """Har qatorda: 'Matn | https://link'. Noto'g'ri bo'lsa ValueError."""
    buttons = []
    for line in raw.strip().splitlines():
        if "|" not in line:
            raise ValueError(line)
        text, url = (p.strip() for p in line.split("|", 1))
        if not text or not url.startswith(("http://", "https://", "tg://")):
            raise ValueError(line)
        buttons.append([text, url])
    return buttons


def build_markup(buttons: Optional[list[list[str]]]) -> Optional[InlineKeyboardMarkup]:
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, url=u)] for t, u in buttons])


def _bar(done: int, total: int) -> str:
    filled = int(10 * done / total) if total else 10
    return "▓" * filled + "░" * (10 - filled)


async def _send_one(bot: Bot, uid: int, src_chat: int, src_msg: int, markup, mode: str) -> bool:
    for _ in range(2):  # FloodWait bo'lsa bir marta qayta urinadi
        try:
            if mode == "fwd":
                await bot.forward_message(uid, src_chat, src_msg)
            else:
                await bot.copy_message(uid, src_chat, src_msg, reply_markup=markup)
            return True
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after + 1)
        except (TelegramForbiddenError, TelegramBadRequest):
            return False
        except Exception as exc:
            log.warning("Broadcast xato (%s): %s", uid, exc)
            return False
    return False


async def _edit(bot: Bot, chat_id: int, msg_id: int, text: str) -> None:
    try:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id)
    except TelegramBadRequest:
        pass


async def run_broadcast(bot: Bot, user_ids: list[int], src_chat: int, src_msg: int,
                        markup, mode: str, status_chat: int, status_msg: int) -> None:
    total, ok, fail, last_edit = len(user_ids), 0, 0, 0.0
    try:
        for i, uid in enumerate(user_ids, 1):
            if await _send_one(bot, uid, src_chat, src_msg, markup, mode):
                ok += 1
            else:
                fail += 1
            await asyncio.sleep(0.05)  # ~20 xabar/soniya (Telegram limiti ichida)
            if time.monotonic() - last_edit > 2 and i != total:
                last_edit = time.monotonic()
                await _edit(bot, status_chat, status_msg,
                            f"📤 Yuborilmoqda...\n{_bar(i, total)} {i * 100 // total}%\n✅ {ok}  ❌ {fail}  📊 {i}/{total}")
        await _edit(bot, status_chat, status_msg,
                    f"✅ Yuborish yakunlandi!\n{_bar(total, total)} 100%\n\n"
                    f"✅ Yetkazildi: {ok}\n❌ Yetkazilmadi: {fail}\n📊 Jami: {total}")
    except Exception as exc:
        await report_error(bot, exc, where="broadcast")
