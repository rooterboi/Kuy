"""Top Chart, Saralanganlar, Lyrics va audio effektlar."""
import uuid

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, Message

from config import TMP_DIR
from database.db import Database
from utils.alerts import report_error
from utils.downloader import JOB_SEMAPHORE
from utils.ffmpeg_effects import FILTERS, LABELS, apply_effect, get_duration
from utils.helpers import esc, safe_remove, split_text
from utils.i18n import all_variants, t
from utils.keyboards import chart_kb, favorites_kb, track_kb
from utils.lyrics import fetch_lyrics

router = Router(name="features")


# ------------------------------------------------------------------ Top 10
@router.message(F.text.in_(all_variants("btn_chart")))
async def show_chart(message: Message, db: Database, lang: str):
    tracks = await db.top_tracks(10)
    if not tracks:
        await message.answer(t(lang, "chart_empty"))
        return
    await message.answer(t(lang, "chart_title"), reply_markup=chart_kb(tracks))


# ------------------------------------------------------------------ Favorites
@router.message(F.text.in_(all_variants("btn_fav")))
async def show_favorites(message: Message, db: Database, lang: str):
    items = await db.list_favorites(message.from_user.id)
    if not items:
        await message.answer(t(lang, "fav_empty"))
        return
    await message.answer(t(lang, "fav_title"), reply_markup=favorites_kb(items))


@router.callback_query(F.data.startswith("fav:"))
async def add_favorite(cb: CallbackQuery, db: Database, lang: str):
    track_id = int(cb.data.split(":")[1])
    added = await db.add_favorite(cb.from_user.id, track_id)
    await cb.answer(t(lang, "fav_added" if added else "fav_exists"), show_alert=not added)


@router.callback_query(F.data.startswith("fp:"))
async def play_favorite(cb: CallbackQuery, bot: Bot, db: Database, lang: str):
    track = await db.get_track(int(cb.data.split(":")[1]))
    await cb.answer()
    if not track or not track["file_id"]:
        return
    await bot.send_audio(cb.from_user.id, track["file_id"], reply_markup=track_kb(lang, track["id"]))


@router.callback_query(F.data.startswith("fd:"))
async def delete_favorite(cb: CallbackQuery, db: Database, lang: str):
    await db.remove_favorite(cb.from_user.id, int(cb.data.split(":")[1]))
    await cb.answer(t(lang, "fav_removed"))
    items = await db.list_favorites(cb.from_user.id)
    if not items:
        await cb.message.edit_text(t(lang, "fav_empty"))
    else:
        await cb.message.edit_reply_markup(reply_markup=favorites_kb(items))


# ------------------------------------------------------------------ Lyrics
@router.callback_query(F.data.startswith("ly:"))
async def show_lyrics(cb: CallbackQuery, db: Database, lang: str):
    track = await db.get_track(int(cb.data.split(":")[1]))
    if not track:
        await cb.answer()
        return
    await cb.answer(t(lang, "lyrics_searching"))
    text = await fetch_lyrics(track["title"], track["artist"])
    if not text:
        await cb.message.answer(t(lang, "lyrics_not_found"))
        return
    chunks = split_text(text)
    chunks[0] = f"📝 <b>{esc(track['title'])}</b>\n\n" + esc(chunks[0])
    for i, chunk in enumerate(chunks):
        await cb.message.answer(chunk if i == 0 else esc(chunk))


# ------------------------------------------------------------------ Audio effektlar
@router.callback_query(F.data.startswith("fx:"))
async def apply_audio_effect(cb: CallbackQuery, bot: Bot, db: Database, lang: str):
    _, mode, raw_id = cb.data.split(":")
    track = await db.get_track(int(raw_id))
    if mode not in FILTERS or not track or not track["file_id"]:
        await cb.answer()
        return
    await cb.answer(t(lang, "fx_processing"))
    status = await cb.message.answer(t(lang, "fx_processing"))

    uid = uuid.uuid4().hex
    src, dst = TMP_DIR / f"{uid}_src.mp3", TMP_DIR / f"{uid}_out.mp3"
    try:
        async with JOB_SEMAPHORE:
            await bot.download(track["file_id"], destination=src)
            await apply_effect(src, dst, mode)
        duration = await get_duration(dst)
        await bot.send_audio(
            cb.from_user.id,
            FSInputFile(dst, filename=f"{track['title'][:60]} [{LABELS[mode]}].mp3"),
            title=f"{track['title']} [{LABELS[mode]}]",
            performer=track["artist"],
            duration=duration or None,
        )
        await status.delete()
    except TelegramBadRequest as exc:
        if "too big" in str(exc).lower():
            await status.edit_text(t(lang, "file_limit"))
        else:
            code = await report_error(bot, exc, user=cb.from_user, where=f"effect {mode}")
            await status.edit_text(t(lang, "error", code=code))
    except Exception as exc:
        code = await report_error(bot, exc, user=cb.from_user, where=f"effect {mode}")
        await status.edit_text(t(lang, "error", code=code))
    finally:
        safe_remove(src, dst)
