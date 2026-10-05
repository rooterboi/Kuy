"""Admin panel: statistika, broadcast, majburiy obuna, ban va tizim diagnostikasi."""
import asyncio

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message, TelegramObject

from config import ADMIN_IDS, LOG_FILE
from database.db import Database
from utils import system
from utils.broadcast import BACKGROUND_TASKS, build_markup, parse_buttons, run_broadcast
from utils.helpers import esc, human_size
from utils.keyboards import (
    admin_back_kb, admin_channels_kb, admin_home_kb, admin_restart_kb,
    admin_sys_kb, broadcast_confirm_kb,
)
from utils.logger import get_logger

log = get_logger(__name__)


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id in ADMIN_IDS)


class Admin(StatesGroup):
    add_channel = State()
    block = State()
    unblock = State()
    bc_content = State()
    bc_buttons = State()


router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

HOME_TEXT = "🛠 <b>Admin panel</b>"


# ------------------------------------------------------------------ bosh menyu
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HOME_TEXT, reply_markup=admin_home_kb())


@router.callback_query(F.data == "adm:home")
async def home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(HOME_TEXT, reply_markup=admin_home_kb())
    await cb.answer()


# ------------------------------------------------------------------ statistika
@router.callback_query(F.data == "adm:stats")
async def stats(cb: CallbackQuery, db: Database):
    s = await db.get_stats()
    top_tracks = "\n".join(f"{i}. {esc(t['title'][:45])} — {t['plays']}" for i, t in enumerate(s["top_tracks"], 1)) or "—"
    top_queries = "\n".join(f"{i}. {esc(q['query'][:45])} — {q['hits']}" for i, q in enumerate(s["top_queries"], 1)) or "—"
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{s['users']}</b>\n"
        f"🔥 Bugungi faollar: <b>{s['active_today']}</b>\n"
        f"🚫 Bloklanganlar: <b>{s['banned']}</b>\n"
        f"🎵 Bazadagi treklar: <b>{s['tracks']}</b>\n\n"
        f"🏆 <b>Eng ko‘p yuklangan:</b>\n{top_tracks}\n\n"
        f"🔎 <b>Eng ko‘p qidirilgan:</b>\n{top_queries}"
    )
    await cb.message.edit_text(text, reply_markup=admin_back_kb())
    await cb.answer()


# ------------------------------------------------------------------ majburiy obuna
async def _channels_text(db: Database) -> tuple[str, list[dict]]:
    channels = await db.list_channels()
    body = "\n".join(f"• {esc(c['title'])} (<code>{c['chat_id']}</code>)" for c in channels) or "Hozircha kanallar yo‘q."
    return f"🔒 <b>Majburiy obuna kanallari:</b>\n\n{body}", channels


@router.callback_query(F.data == "adm:channels")
async def channels(cb: CallbackQuery, db: Database):
    text, chs = await _channels_text(db)
    await cb.message.edit_text(text, reply_markup=admin_channels_kb(chs))
    await cb.answer()


@router.callback_query(F.data.startswith("adm:chdel:"))
async def channel_delete(cb: CallbackQuery, db: Database):
    await db.remove_channel(int(cb.data.split(":")[2]))
    text, chs = await _channels_text(db)
    await cb.message.edit_text(text, reply_markup=admin_channels_kb(chs))
    await cb.answer("🗑 O‘chirildi")


@router.callback_query(F.data == "adm:chadd")
async def channel_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Admin.add_channel)
    await cb.message.edit_text(
        "➕ Kanal @username yoki ID (-100...) sini yuboring, yoki kanaldan xabarni forward qiling.\n\n"
        "⚠️ Bot kanalda <b>admin</b> bo‘lishi shart.",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(Admin.add_channel)
async def channel_add_finish(message: Message, bot: Bot, db: Database, state: FSMContext):
    ref = None
    origin = message.forward_origin
    if origin is not None and getattr(origin, "chat", None):
        ref = origin.chat.id
    elif message.text:
        raw = message.text.strip().replace("https://t.me/", "@").replace("t.me/", "@")
        ref = int(raw) if raw.lstrip("-").isdigit() else raw
    if ref is None:
        await message.answer("❌ Noto‘g‘ri format. Qaytadan yuboring.")
        return
    try:
        chat = await bot.get_chat(ref)
        me = await bot.get_chat_member(chat.id, bot.id)
        if me.status not in ("administrator", "creator"):
            await message.answer("❌ Bot bu kanalda admin emas. Avval botni admin qiling.")
            return
        url = f"https://t.me/{chat.username}" if chat.username else (
            chat.invite_link or await bot.export_chat_invite_link(chat.id))
        await db.add_channel(chat.id, chat.title or str(chat.id), url)
    except TelegramAPIError as exc:
        await message.answer(f"❌ Xatolik: {esc(exc)}")
        return
    await state.clear()
    text, chs = await _channels_text(db)
    await message.answer("✅ Kanal qo‘shildi!\n\n" + text, reply_markup=admin_channels_kb(chs))


# ------------------------------------------------------------------ ban / unban
@router.callback_query(F.data.in_({"adm:block", "adm:unblock"}))
async def ban_start(cb: CallbackQuery, state: FSMContext):
    blocking = cb.data == "adm:block"
    await state.set_state(Admin.block if blocking else Admin.unblock)
    await cb.message.edit_text(
        f"{'🚫 Bloklanadigan' if blocking else '✅ Blokdan chiqariladigan'} foydalanuvchi ID sini yuboring:",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(Admin.block)
@router.message(Admin.unblock)
async def ban_finish(message: Message, db: Database, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("❌ Faqat raqamli ID yuboring.")
        return
    blocking = await state.get_state() == Admin.block.state
    uid = int(raw)
    if uid in ADMIN_IDS:
        await message.answer("❌ Adminni bloklab bo‘lmaydi.")
        return
    changed = await db.set_ban(uid, blocking)
    await state.clear()
    if not changed:
        await message.answer("❌ Bunday foydalanuvchi bazada topilmadi.", reply_markup=admin_back_kb())
        return
    await message.answer(f"{'🚫 Bloklandi' if blocking else '✅ Blokdan chiqarildi'}: <code>{uid}</code>",
                         reply_markup=admin_back_kb())


# ------------------------------------------------------------------ broadcast
@router.callback_query(F.data == "adm:bc")
async def bc_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Admin.bc_content)
    await cb.message.edit_text(
        "📢 Yuboriladigan xabarni jo‘nating (matn, rasm, video yoki forward).",
        reply_markup=admin_back_kb(),
    )
    await cb.answer()


@router.message(Admin.bc_content)
async def bc_content(message: Message, state: FSMContext):
    await state.update_data(src_chat=message.chat.id, src_msg=message.message_id)
    await state.set_state(Admin.bc_buttons)
    await message.answer(
        "🔘 Inline tugmalar kerak bo‘lsa, har qatorga bittadan yozing:\n"
        "<code>Matn | https://link.uz</code>\n\nTugma kerak bo‘lmasa <b>-</b> yuboring.",
        reply_markup=admin_back_kb(),
    )


@router.message(Admin.bc_buttons)
async def bc_buttons(message: Message, bot: Bot, db: Database, state: FSMContext):
    raw = (message.text or "").strip()
    buttons = []
    if raw != "-":
        try:
            buttons = parse_buttons(raw)
        except ValueError:
            await message.answer("❌ Format noto‘g‘ri. Misol: <code>Kanal | https://t.me/kanal</code>")
            return
    await state.update_data(buttons=buttons)
    data = await state.get_data()
    users = len(await db.all_user_ids())
    # Ko'rib chiqish (preview)
    await bot.copy_message(message.chat.id, data["src_chat"], data["src_msg"], reply_markup=build_markup(buttons))
    await message.answer(f"👆 Shu xabar <b>{users}</b> ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
                         reply_markup=broadcast_confirm_kb())


@router.callback_query(F.data.startswith("adm:bcgo:"))
async def bc_go(cb: CallbackQuery, bot: Bot, db: Database, state: FSMContext):
    mode = cb.data.split(":")[2]
    data = await state.get_data()
    if "src_msg" not in data:
        await cb.answer("Sessiya tugagan, qaytadan boshlang.", show_alert=True)
        return
    users = await db.all_user_ids()
    status = await cb.message.edit_text("📤 Yuborish boshlandi...")
    task = asyncio.create_task(run_broadcast(
        bot, users, data["src_chat"], data["src_msg"], build_markup(data.get("buttons")),
        mode, status.chat.id, status.message_id,
    ))
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)
    await state.clear()
    await cb.answer()


# ------------------------------------------------------------------ tizim sozligi va loglar
@router.callback_query(F.data == "adm:sys")
async def sys_info(cb: CallbackQuery):
    total, used, free = system.disk_info()
    mem = system.memory_info()
    mem_line = f"{human_size(mem[1])} / {human_size(mem[0])}" if mem else "—"
    log_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    text = (
        "🛠 <b>Tizim sozligi</b>\n\n"
        f"⏱ Ish vaqti: {system.uptime_str()}\n"
        f"💾 Disk: {human_size(used)} / {human_size(total)} (bo‘sh: {human_size(free)})\n"
        f"🧠 Xotira: {mem_line}\n"
        f"🗂 Kesh (tmp): {human_size(system.tmp_size())}\n"
        f"📦 yt-dlp: <code>{system.get_ytdlp_version()}</code>\n"
        f"📄 Log hajmi: {human_size(log_size)}"
    )
    await cb.message.edit_text(text, reply_markup=admin_sys_kb())
    await cb.answer()


@router.callback_query(F.data == "adm:logview")
async def log_view(cb: CallbackQuery):
    tail = system.log_tail(25) or "Log bo‘sh."
    await cb.message.answer(f"<pre>{esc(tail[-3500:])}</pre>")
    await cb.answer()


@router.callback_query(F.data == "adm:logfile")
async def log_file(cb: CallbackQuery, bot: Bot):
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        await cb.answer("Log bo‘sh.", show_alert=True)
        return
    await bot.send_document(cb.from_user.id, FSInputFile(LOG_FILE, filename="bot.log"))
    await cb.answer()


@router.callback_query(F.data == "adm:logclear")
async def log_clear(cb: CallbackQuery):
    system.clear_log()
    await cb.answer("🗑 Log tozalandi", show_alert=True)


# ------------------------------------------------------------------ yt-dlp / kesh / restart
@router.callback_query(F.data == "adm:ytdlp")
async def ytdlp_update(cb: CallbackQuery):
    await cb.answer()
    old = system.get_ytdlp_version()
    msg = await cb.message.edit_text("⏳ yt-dlp yangilanmoqda (pip install --upgrade yt-dlp)...")
    ok, out = await system.update_ytdlp()
    new = system.get_ytdlp_version()
    if ok:
        text = (f"✅ yt-dlp yangilandi: <code>{old}</code> → <code>{new}</code>\n\n"
                "Yangi versiya ishlashi uchun botni qayta yuklang.")
        await msg.edit_text(text, reply_markup=admin_restart_kb())
    else:
        await msg.edit_text(f"❌ Yangilashda xatolik:\n<pre>{esc(out[-600:])}</pre>", reply_markup=admin_back_kb())


@router.callback_query(F.data == "adm:clean")
async def clean_cache(cb: CallbackQuery):
    count, freed = system.clean_tmp(0)
    await cb.answer(f"🧹 {count} ta fayl o‘chirildi, {human_size(freed)} bo‘shatildi", show_alert=True)


@router.callback_query(F.data == "adm:restart")
async def restart(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text("♻️ Bot qayta ishga tushmoqda...")
    except TelegramBadRequest:
        pass
    await asyncio.sleep(2)  # polling offset tasdiqlanishi uchun
    log.info("Admin %s botni qayta yukladi", cb.from_user.id)
    system.restart_bot()
