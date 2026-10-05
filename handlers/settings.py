"""Sozlamalar menyusi (tilni istalgan vaqtda o'zgartirish)."""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from utils.i18n import all_variants, t
from utils.keyboards import language_kb, settings_kb

router = Router(name="settings")


@router.message(F.text.in_(all_variants("btn_settings")))
async def open_settings(message: Message, lang: str):
    await message.answer(t(lang, "settings_title"), reply_markup=settings_kb(lang))


@router.callback_query(F.data == "settings:lang")
async def change_language(cb: CallbackQuery, lang: str):
    await cb.message.edit_text(t(lang, "choose_lang"), reply_markup=language_kb())
    await cb.answer()
