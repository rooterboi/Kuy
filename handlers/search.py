"""Matn orqali YouTube qidiruvi va tanlangan qo'shiqni audio ko'rinishida yuklash."""
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import SEARCH_RESULTS
from database.db import Database
from utils.alerts import report_error
from utils.downloader import JOB_SEMAPHORE, FileTooBigError, download_audio, search_youtube
from utils.ffmpeg_effects import get_duration
from utils.helpers import esc, safe_remove
from utils.i18n import t
from utils.keyboards import results_kb, track_kb

router = Router(name="search")


@router.message(F.text, ~F.text.startswith("/"))
async def on_text(message: Message, bot: Bot, db: Database, lang: str):
    query = message.text.strip()[:100]
    if len(query) < 2:
        return
    status = await message.answer(t(lang, "searching"))
    try:
        results = await search_youtube(query, limit=SEARCH_RESULTS)
    except Exception as exc:
        code = await report_error(bot, exc, user=message.from_user, where=f"search: {query}")
        await status.edit_text(t(lang, "error", code=code))
        return
    if not results:
        await status.edit_text(t(lang, "no_results"))
        return
    await db.log_search(query)
    await status.edit_text(t(lang, "results_title", query=esc(query)), reply_markup=results_kb(results))


@router.callback_query(F.data.startswith("yt:"))
async def on_pick(cb: CallbackQuery, bot: Bot, db: Database, lang: str):
    video_id = cb.data.split(":", 1)[1]
    await cb.answer()
    me = await bot.me()
    chat_id = cb.from_user.id

    # 1) Kesh: avval yuklangan bo'lsa Telegram file_id orqali bir zumda yuboramiz
    track = await db.get_track_by_video(video_id)
    if track and track["file_id"]:
        try:
            await bot.send_audio(chat_id, track["file_id"], caption=f"🎵 @{me.username}",
                                 reply_markup=track_kb(lang, track["id"]))
            await db.inc_plays(track["id"])
            return
        except TelegramBadRequest:
            pass  # file_id eskirgan -> qaytadan yuklaymiz

    # 2) Yangi yuklash
    status = await bot.send_message(chat_id, t(lang, "downloading"))
    media = None
    try:
        async with JOB_SEMAPHORE:
            media = await download_audio(f"https://www.youtube.com/watch?v={video_id}")
        await status.edit_text(t(lang, "uploading"))

        duration = media.duration or await get_duration(media.path)
        track_id = await db.upsert_track(video_id, media.title, media.uploader, duration)
        sent = await bot.send_audio(
            chat_id, FSInputFile(media.path, filename=f"{media.title[:60]}.mp3"),
            title=media.title, performer=media.uploader, duration=duration or None,
            caption=f"🎵 @{me.username}", reply_markup=track_kb(lang, track_id),
        )
        await db.set_track_file(track_id, sent.audio.file_id)
        await db.inc_plays(track_id)
        await status.delete()
    except FileTooBigError:
        await status.edit_text(t(lang, "too_big"))
    except Exception as exc:
        code = await report_error(bot, exc, user=cb.from_user, where=f"yt-audio: {video_id}")
        await status.edit_text(t(lang, "error", code=code))
    finally:
        if media:
            safe_remove(media.path)
