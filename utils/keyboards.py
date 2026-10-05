"""Barcha klaviaturalar (Reply va Inline) bir joyda."""
from aiogram.types import (
    InlineKeyboardButton as Btn,
    InlineKeyboardMarkup as Markup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from utils.helpers import fmt_duration
from utils.i18n import t


# ------------------------------------------------------------------ foydalanuvchi
def language_kb() -> Markup:
    return Markup(inline_keyboard=[
        [Btn(text="🇺🇿 O‘zbekcha", callback_data="lang:uz")],
        [Btn(text="🇷🇺 Русский", callback_data="lang:ru")],
        [Btn(text="🇬🇧 English", callback_data="lang:en")],
    ])


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_chart")), KeyboardButton(text=t(lang, "btn_fav"))],
            [KeyboardButton(text=t(lang, "btn_shazam")), KeyboardButton(text=t(lang, "btn_settings"))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t(lang, "placeholder"),
    )


def settings_kb(lang: str) -> Markup:
    return Markup(inline_keyboard=[[Btn(text=t(lang, "btn_change_lang"), callback_data="settings:lang")]])


def subscribe_kb(lang: str, channels: list[dict]) -> Markup:
    rows = [[Btn(text=f"📢 {ch['title']}", url=ch["url"])] for ch in channels]
    rows.append([Btn(text=t(lang, "btn_check_sub"), callback_data="chk_sub")])
    return Markup(inline_keyboard=rows)


def link_kb(lang: str, link_id: int) -> Markup:
    return Markup(inline_keyboard=[[
        Btn(text=t(lang, "btn_video"), callback_data=f"dl:v:{link_id}"),
        Btn(text=t(lang, "btn_audio"), callback_data=f"dl:a:{link_id}"),
    ]])


def results_kb(results: list[dict]) -> Markup:
    rows = [
        [Btn(text=f"{i}. {r['title'][:48]} • {fmt_duration(r['duration'])}", callback_data=f"yt:{r['id']}")]
        for i, r in enumerate(results, 1)
    ]
    return Markup(inline_keyboard=rows)


def track_kb(lang: str, track_id: int) -> Markup:
    """Audio ostidagi tugmalar: saqlash, matn va effektlar."""
    return Markup(inline_keyboard=[
        [Btn(text=t(lang, "btn_fav_add"), callback_data=f"fav:{track_id}"),
         Btn(text=t(lang, "btn_lyrics"), callback_data=f"ly:{track_id}")],
        [Btn(text="⏩ 1.25x", callback_data=f"fx:s125:{track_id}"),
         Btn(text="⏩ 1.5x", callback_data=f"fx:s150:{track_id}"),
         Btn(text="🐢 0.8x", callback_data=f"fx:slow:{track_id}")],
        [Btn(text="🔊 BASS", callback_data=f"fx:bass:{track_id}"),
         Btn(text="🎧 8D", callback_data=f"fx:8d:{track_id}")],
    ])


def chart_kb(tracks: list[dict]) -> Markup:
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    rows = [
        [Btn(text=f"{medals[i]} {tr['title'][:46]} ({tr['plays']})", callback_data=f"yt:{tr['video_id']}")]
        for i, tr in enumerate(tracks)
    ]
    return Markup(inline_keyboard=rows)


def favorites_kb(items: list[dict]) -> Markup:
    rows = [
        [Btn(text=f"🎵 {it['title'][:40]}", callback_data=f"fp:{it['id']}"),
         Btn(text="🗑", callback_data=f"fd:{it['id']}")]
        for it in items
    ]
    return Markup(inline_keyboard=rows)


# ------------------------------------------------------------------ admin
def admin_home_kb() -> Markup:
    return Markup(inline_keyboard=[
        [Btn(text="📊 Statistika", callback_data="adm:stats"),
         Btn(text="📢 Reklama yuborish", callback_data="adm:bc")],
        [Btn(text="🔒 Majburiy obuna", callback_data="adm:channels")],
        [Btn(text="🚫 Bloklash", callback_data="adm:block"),
         Btn(text="✅ Unblok", callback_data="adm:unblock")],
        [Btn(text="🛠 Tizim Sozligi va Loglar", callback_data="adm:sys")],
        [Btn(text="🔄 yt-dlp ni Yangilash", callback_data="adm:ytdlp"),
         Btn(text="🧹 Keshlarni Tozalash", callback_data="adm:clean")],
        [Btn(text="♻️ Botni Qayta Yuklash", callback_data="adm:restart")],
    ])


def admin_back_kb() -> Markup:
    return Markup(inline_keyboard=[[Btn(text="⬅️ Admin panel", callback_data="adm:home")]])


def admin_sys_kb() -> Markup:
    return Markup(inline_keyboard=[
        [Btn(text="👁 Oxirgi loglar", callback_data="adm:logview"),
         Btn(text="📄 Log faylni olish", callback_data="adm:logfile")],
        [Btn(text="🗑 Logni o‘chirish", callback_data="adm:logclear")],
        [Btn(text="⬅️ Admin panel", callback_data="adm:home")],
    ])


def admin_channels_kb(channels: list[dict]) -> Markup:
    rows = [[Btn(text=f"🗑 {ch['title'][:40]}", callback_data=f"adm:chdel:{ch['chat_id']}")] for ch in channels]
    rows.append([Btn(text="➕ Kanal qo‘shish", callback_data="adm:chadd")])
    rows.append([Btn(text="⬅️ Admin panel", callback_data="adm:home")])
    return Markup(inline_keyboard=rows)


def admin_restart_kb() -> Markup:
    return Markup(inline_keyboard=[
        [Btn(text="♻️ Hozir qayta yuklash", callback_data="adm:restart")],
        [Btn(text="⬅️ Admin panel", callback_data="adm:home")],
    ])


def broadcast_confirm_kb() -> Markup:
    return Markup(inline_keyboard=[
        [Btn(text="✅ Yuborish (nusxa)", callback_data="adm:bcgo:copy")],
        [Btn(text="↪️ Forward qilib yuborish", callback_data="adm:bcgo:fwd")],
        [Btn(text="❌ Bekor qilish", callback_data="adm:home")],
    ])
