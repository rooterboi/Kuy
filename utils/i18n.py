"""Ko'p tillilik: uz / ru / en matnlari."""
from config import DEFAULT_LANG

TEXTS: dict[str, dict[str, str]] = {
    # ============================================================ O'ZBEKCHA
    "uz": {
        "choose_lang": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "lang_saved": "✅ Til o‘zgartirildi: 🇺🇿 O‘zbekcha",
        "welcome": (
            "👋 Salom, <b>{name}</b>!\n\n"
            "🎵 Men musiqa va video yuklovchi botman:\n"
            "• Qo‘shiq yoki ijrochi nomini yozing\n"
            "• Instagram / TikTok / YouTube Shorts / Pinterest havolasini yuboring\n"
            "• Ovozli xabar yuboring — musiqani aniqlayman 🎙"
        ),
        "placeholder": "Qo‘shiq nomi yoki havola...",
        "btn_chart": "🔥 Top 10",
        "btn_fav": "⭐ Saralanganlar",
        "btn_shazam": "🎙 Musiqani aniqlash",
        "btn_settings": "⚙️ Sozlamalar",
        "settings_title": "⚙️ <b>Sozlamalar</b>",
        "btn_change_lang": "🌐 Tilni o‘zgartirish",
        "must_join": "🔒 Botdan foydalanish uchun quyidagi kanallarga a’zo bo‘ling, so‘ng «Tekshirish» tugmasini bosing:",
        "btn_check_sub": "✅ Tekshirish",
        "not_subscribed": "❌ Siz hali barcha kanallarga a’zo bo‘lmagansiz!",
        "subscribed_ok": "✅ Rahmat! Endi botdan foydalanishingiz mumkin.",
        "banned": "🚫 Siz bloklangansiz.",
        "searching": "🔎 Qidirilmoqda...",
        "no_results": "😕 Hech narsa topilmadi. Boshqa so‘z bilan urinib ko‘ring.",
        "results_title": "🎶 <b>«{query}»</b> bo‘yicha natijalar:",
        "downloading": "⏳ Yuklab olinmoqda...",
        "uploading": "📤 Yuborilmoqda...",
        "too_big": "⚠️ Fayl hajmi Telegram limitidan (50 MB) oshib ketdi.",
        "file_limit": "⚠️ Fayl juda katta (Telegram botlar uchun 20 MB dan ortiq faylni yuklab bo‘lmaydi).",
        "error": "❌ Xatolik yuz berdi. Xato kodi: <code>{code}</code>\nAdministratorga xabar yuborildi.",
        "link_found": "🔗 Havola aniqlandi. Formatni tanlang:",
        "unsupported_link": "⚠️ Bu havola qo‘llab-quvvatlanmaydi. Instagram, TikTok, YouTube yoki Pinterest havolasini yuboring.",
        "btn_video": "🎬 Video (HD)",
        "btn_audio": "🎵 MP3",
        "link_expired": "⌛ Havola eskirgan, qaytadan yuboring.",
        "chart_title": "🔥 <b>Eng mashhur 10 ta musiqa:</b>",
        "chart_empty": "📭 Hozircha reyting bo‘sh. Birinchi bo‘lib musiqa yuklab oling!",
        "fav_title": "⭐ <b>Saralanganlar</b> (tinglash uchun bosing, 🗑 — o‘chirish):",
        "fav_empty": "📭 Saralanganlar ro‘yxati bo‘sh. Musiqa ostidagi ❤️ tugmasini bosing.",
        "fav_added": "❤️ Saralanganlarga qo‘shildi!",
        "fav_exists": "ℹ️ Bu qo‘shiq allaqachon ro‘yxatda.",
        "fav_removed": "🗑 O‘chirildi.",
        "btn_fav_add": "❤️ Saqlash",
        "btn_lyrics": "📝 Matn",
        "lyrics_searching": "🔎 Matn qidirilmoqda...",
        "lyrics_not_found": "😕 Bu qo‘shiq matni topilmadi.",
        "fx_processing": "🎛 Effekt qo‘llanmoqda...",
        "shazam_help": "🎙 Ovozli xabar yoki audio fayl yuboring — men qaysi musiqa ekanini aniqlayman.",
        "shazam_listening": "🎧 Tinglanmoqda...",
        "shazam_not_found": "😕 Musiqa aniqlanmadi. Boshqaroq, aniqroq parcha yuboring.",
        "shazam_found": "🎧 <b>{title}</b>\n👤 {artist}\n\nYuklab olish uchun variantni tanlang:",
    },
    # ============================================================ RUSSKIY
    "ru": {
        "choose_lang": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "lang_saved": "✅ Язык изменён: 🇷🇺 Русский",
        "welcome": (
            "👋 Привет, <b>{name}</b>!\n\n"
            "🎵 Я бот для скачивания музыки и видео:\n"
            "• Напишите название песни или исполнителя\n"
            "• Отправьте ссылку Instagram / TikTok / YouTube Shorts / Pinterest\n"
            "• Отправьте голосовое — я распознаю музыку 🎙"
        ),
        "placeholder": "Название песни или ссылка...",
        "btn_chart": "🔥 Топ 10",
        "btn_fav": "⭐ Избранное",
        "btn_shazam": "🎙 Распознать музыку",
        "btn_settings": "⚙️ Настройки",
        "settings_title": "⚙️ <b>Настройки</b>",
        "btn_change_lang": "🌐 Сменить язык",
        "must_join": "🔒 Чтобы пользоваться ботом, подпишитесь на каналы ниже и нажмите «Проверить»:",
        "btn_check_sub": "✅ Проверить",
        "not_subscribed": "❌ Вы ещё не подписались на все каналы!",
        "subscribed_ok": "✅ Спасибо! Теперь вы можете пользоваться ботом.",
        "banned": "🚫 Вы заблокированы.",
        "searching": "🔎 Поиск...",
        "no_results": "😕 Ничего не найдено. Попробуйте другой запрос.",
        "results_title": "🎶 Результаты по запросу <b>«{query}»</b>:",
        "downloading": "⏳ Скачиваю...",
        "uploading": "📤 Отправляю...",
        "too_big": "⚠️ Размер файла превышает лимит Telegram (50 МБ).",
        "file_limit": "⚠️ Файл слишком большой (боты Telegram не могут скачивать файлы больше 20 МБ).",
        "error": "❌ Произошла ошибка. Код ошибки: <code>{code}</code>\nАдминистратор уведомлён.",
        "link_found": "🔗 Ссылка распознана. Выберите формат:",
        "unsupported_link": "⚠️ Эта ссылка не поддерживается. Отправьте ссылку Instagram, TikTok, YouTube или Pinterest.",
        "btn_video": "🎬 Видео (HD)",
        "btn_audio": "🎵 MP3",
        "link_expired": "⌛ Ссылка устарела, отправьте её снова.",
        "chart_title": "🔥 <b>Топ 10 самых популярных треков:</b>",
        "chart_empty": "📭 Рейтинг пока пуст. Скачайте музыку первым!",
        "fav_title": "⭐ <b>Избранное</b> (нажмите, чтобы послушать, 🗑 — удалить):",
        "fav_empty": "📭 Избранное пусто. Нажмите ❤️ под треком.",
        "fav_added": "❤️ Добавлено в избранное!",
        "fav_exists": "ℹ️ Этот трек уже в списке.",
        "fav_removed": "🗑 Удалено.",
        "btn_fav_add": "❤️ Сохранить",
        "btn_lyrics": "📝 Текст",
        "lyrics_searching": "🔎 Ищу текст...",
        "lyrics_not_found": "😕 Текст этой песни не найден.",
        "fx_processing": "🎛 Применяю эффект...",
        "shazam_help": "🎙 Отправьте голосовое сообщение или аудиофайл — я определю, что это за музыка.",
        "shazam_listening": "🎧 Слушаю...",
        "shazam_not_found": "😕 Музыка не распознана. Отправьте более чёткий фрагмент.",
        "shazam_found": "🎧 <b>{title}</b>\n👤 {artist}\n\nВыберите вариант для скачивания:",
    },
    # ============================================================ ENGLISH
    "en": {
        "choose_lang": "🌐 Tilni tanlang / Выберите язык / Choose language:",
        "lang_saved": "✅ Language changed: 🇬🇧 English",
        "welcome": (
            "👋 Hi, <b>{name}</b>!\n\n"
            "🎵 I'm a music & video downloader bot:\n"
            "• Type a song or artist name\n"
            "• Send an Instagram / TikTok / YouTube Shorts / Pinterest link\n"
            "• Send a voice note — I'll recognize the music 🎙"
        ),
        "placeholder": "Song name or link...",
        "btn_chart": "🔥 Top 10",
        "btn_fav": "⭐ Favorites",
        "btn_shazam": "🎙 Recognize music",
        "btn_settings": "⚙️ Settings",
        "settings_title": "⚙️ <b>Settings</b>",
        "btn_change_lang": "🌐 Change language",
        "must_join": "🔒 To use the bot, join the channels below and press “Check”:",
        "btn_check_sub": "✅ Check",
        "not_subscribed": "❌ You haven't joined all channels yet!",
        "subscribed_ok": "✅ Thanks! You can use the bot now.",
        "banned": "🚫 You are banned.",
        "searching": "🔎 Searching...",
        "no_results": "😕 Nothing found. Try different keywords.",
        "results_title": "🎶 Results for <b>“{query}”</b>:",
        "downloading": "⏳ Downloading...",
        "uploading": "📤 Uploading...",
        "too_big": "⚠️ The file exceeds Telegram's limit (50 MB).",
        "file_limit": "⚠️ File is too large (Telegram bots can't download files over 20 MB).",
        "error": "❌ Something went wrong. Error code: <code>{code}</code>\nThe administrator has been notified.",
        "link_found": "🔗 Link detected. Choose a format:",
        "unsupported_link": "⚠️ This link is not supported. Send an Instagram, TikTok, YouTube or Pinterest link.",
        "btn_video": "🎬 Video (HD)",
        "btn_audio": "🎵 MP3",
        "link_expired": "⌛ The link has expired, please send it again.",
        "chart_title": "🔥 <b>Top 10 most popular tracks:</b>",
        "chart_empty": "📭 The chart is empty for now. Be the first to download music!",
        "fav_title": "⭐ <b>Favorites</b> (tap to play, 🗑 to remove):",
        "fav_empty": "📭 Your favorites are empty. Tap ❤️ under a track.",
        "fav_added": "❤️ Added to favorites!",
        "fav_exists": "ℹ️ This track is already in your list.",
        "fav_removed": "🗑 Removed.",
        "btn_fav_add": "❤️ Save",
        "btn_lyrics": "📝 Lyrics",
        "lyrics_searching": "🔎 Looking for lyrics...",
        "lyrics_not_found": "😕 Lyrics for this song were not found.",
        "fx_processing": "🎛 Applying effect...",
        "shazam_help": "🎙 Send a voice note or an audio file — I'll tell you what music it is.",
        "shazam_listening": "🎧 Listening...",
        "shazam_not_found": "😕 Couldn't recognize the music. Send a clearer fragment.",
        "shazam_found": "🎧 <b>{title}</b>\n👤 {artist}\n\nPick a result to download:",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Kalit bo'yicha tarjima. Topilmasa default tilga, so'ng kalitning o'ziga qaytadi."""
    text = TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key) or TEXTS[DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text


def all_variants(key: str) -> set[str]:
    """Kalitning barcha tillardagi matnlari (tugma matnini filtrlash uchun)."""
    return {texts[key] for texts in TEXTS.values() if key in texts}
