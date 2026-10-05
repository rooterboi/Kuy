"""/start, til tanlash va majburiy obunani tekshirish."""
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from config import SUPPORTED_LANGS
from database.db import Database
from utils.helpers import esc
from utils.i18n import t
from utils.keyboards import language_kb, main_menu
from utils.subscription import check_and_prompt, get_unsubscribed, mark_verified

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, lang: str):
    user = await db.get_user(message.from_user.id)
    if not user or not user["lang"]:
        await message.answer(t(lang, "choose_lang"), reply_markup=language_kb())
        return
    await message.answer(t(lang, "welcome", name=esc(message.from_user.full_name)), reply_markup=main_menu(lang))


@router.callback_query(F.data.startswith("lang:"))
async def on_language(cb: CallbackQuery, bot: Bot, db: Database):
    new_lang = cb.data.split(":")[1]
    if new_lang not in SUPPORTED_LANGS:
        await cb.answer()
        return
    uid = cb.from_user.id
    user = await db.get_user(uid)
    first_time = not (user and user["lang"])
    await db.set_lang(uid, new_lang)
    await cb.answer()
    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass

    if first_time:
        # Birinchi marta: avval majburiy obunani tekshiramiz
        if not await check_and_prompt(bot, db, uid, new_lang):
            return
        await bot.send_message(uid, t(new_lang, "welcome", name=esc(cb.from_user.full_name)),
                               reply_markup=main_menu(new_lang))
    else:
        await bot.send_message(uid, t(new_lang, "lang_saved"), reply_markup=main_menu(new_lang))


@router.callback_query(F.data == "chk_sub")
async def on_check_sub(cb: CallbackQuery, bot: Bot, db: Database, lang: str):
    channels = await db.list_channels()
    missing = await get_unsubscribed(bot, cb.from_user.id, channels)
    if missing:
        await cb.answer(t(lang, "not_subscribed"), show_alert=True)
        return
    mark_verified(cb.from_user.id)
    await cb.answer(t(lang, "subscribed_ok"))
    try:
        await cb.message.delete()
    except TelegramBadRequest:
        pass
    await bot.send_message(cb.from_user.id, t(lang, "welcome", name=esc(cb.from_user.full_name)),
                           reply_markup=main_menu(lang))
