"""Havola (Instagram / TikTok / YouTube Shorts / Pinterest) orqali video va MP3 yuklash."""
import re

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from database.db import Database
from utils.alerts import report_error
from utils.downloader import JOB_SEMAPHORE, FileTooBigError, download_audio, download_video
from utils.helpers import safe_remove
from utils.i18n import t
from utils.keyboards import link_kb

router = Router(name="downloader")

URL_RE = re.compile(r"https?://\S+")
SUPPORTED_RE = re.compile(r"(instagram\.com|tiktok\.com|youtube\.com|youtu\.be|pinterest\.|pin\.it)", re.I)


@router.message(F.text, lambda m: bool(URL_RE.search(m.text)))
async def on_link(message: Message, db: Database, lang: str):
    url = URL_RE.search(message.text).group(0)
    if not SUPPORTED_RE.search(url):
        await message.answer(t(lang, "unsupported_link"))
        return
    link_id = await db.save_link(url)
    await message.answer(t(lang, "link_found"), reply_markup=link_kb(lang, link_id))


@router.callback_query(F.data.startswith("dl:"))
async def on_download(cb: CallbackQuery, bot: Bot, db: Database, lang: str):
    _, kind, raw_id = cb.data.split(":")
    url = await db.get_link(int(raw_id))
    if not url:
        await cb.answer(t(lang, "link_expired"), show_alert=True)
        return
    await cb.answer()
    status = await cb.message.edit_text(t(lang, "downloading"))
    me = await bot.me()
    media = None
    try:
        async with JOB_SEMAPHORE:
            media = await (download_video(url) if kind == "v" else download_audio(url))
        await status.edit_text(t(lang, "uploading"))
        if kind == "v":
            await bot.send_video(
                cb.from_user.id, FSInputFile(media.path),
                caption=f"🎬 @{me.username}", supports_streaming=True,
                duration=media.duration or None, width=media.width, height=media.height,
            )
        else:
            await bot.send_audio(
                cb.from_user.id, FSInputFile(media.path),
                title=media.title, performer=media.uploader,
                duration=media.duration or None, caption=f"🎵 @{me.username}",
            )
        await status.delete()
    except FileTooBigError:
        await status.edit_text(t(lang, "too_big"))
    except Exception as exc:
        code = await report_error(bot, exc, user=cb.from_user, where=f"link-{kind}: {url}")
        await status.edit_text(t(lang, "error", code=code))
    finally:
        if media:
            safe_remove(media.path)
