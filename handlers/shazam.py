"""Ovozli xabar / audio fayl orqali musiqani aniqlash."""
import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from config import SEARCH_RESULTS, TMP_DIR
from utils.alerts import report_error
from utils.downloader import JOB_SEMAPHORE, search_youtube
from utils.helpers import esc, safe_remove
from utils.i18n import all_variants, t
from utils.keyboards import results_kb
from utils.shazam import recognize

router = Router(name="shazam")


@router.message(F.text.in_(all_variants("btn_shazam")))
async def shazam_help(message: Message, lang: str):
    await message.answer(t(lang, "shazam_help"))


@router.message(F.voice | F.audio | F.video_note)
async def on_audio(message: Message, bot: Bot, lang: str):
    media = message.voice or message.audio or message.video_note
    status = await message.answer(t(lang, "shazam_listening"))
    path = TMP_DIR / f"{uuid.uuid4().hex}.audio"
    try:
        async with JOB_SEMAPHORE:
            await bot.download(media, destination=path)
            result = await recognize(str(path))
        if not result:
            await status.edit_text(t(lang, "shazam_not_found"))
            return

        results = await search_youtube(f"{result.artist} {result.title}", limit=min(5, SEARCH_RESULTS))
        text = t(lang, "shazam_found", title=esc(result.title), artist=esc(result.artist))
        markup = results_kb(results) if results else None
        if result.cover:
            await message.answer_photo(result.cover, caption=text, reply_markup=markup)
        else:
            await message.answer(text, reply_markup=markup)
        await status.delete()
    except TelegramBadRequest as exc:
        if "too big" in str(exc).lower():
            await status.edit_text(t(lang, "file_limit"))
        else:
            code = await report_error(bot, exc, user=message.from_user, where="shazam")
            await status.edit_text(t(lang, "error", code=code))
    except Exception as exc:
        code = await report_error(bot, exc, user=message.from_user, where="shazam")
        await status.edit_text(t(lang, "error", code=code))
    finally:
        safe_remove(path)
