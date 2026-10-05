# 🎵 Telegram Music Bot (aiogram 3 + yt-dlp + shazamio)

Musiqa/video yuklovchi, Shazam, lyrics, audio effektlar va to'liq admin panelli Telegram bot.

## Struktura
```
bot.py                 # kirish nuqtasi
config.py              # .env sozlamalari
Dockerfile             # ffmpeg + git + curl bilan
requirements.txt
handlers/              # start, settings, features, shazam, downloader, search, admin, errors
database/              # schema.py, db.py (SQLite)
utils/                 # i18n, keyboards, downloader, ffmpeg_effects, logger, alerts, ...
```

## Lokal ishga tushirish
```bash
pip install -r requirements.txt     # ffmpeg tizimda o'rnatilgan bo'lishi kerak
cp .env.example .env                # BOT_TOKEN va ADMIN_IDS ni to'ldiring
python bot.py
```

## Render.com ga deploy
1. Loyihani GitHub'ga push qiling (`.env` push qilinmaydi).
2. Render → **New + → Web Service** → repo'ni tanlang → **Runtime: Docker**, **Plan: Free**.
3. **Environment** ga qo'shing: `BOT_TOKEN`, `ADMIN_IDS` (vergul bilan).
4. Health Check Path: `/health`.
5. Bepul servis 15 daqiqa so'rov bo'lmasa uxlaydi → https://uptimerobot.com orqali
   `https://<servis>.onrender.com/health` ga har 5 daqiqada ping qo'ying.

## Muhim eslatmalar
- **Render bepul diskı vaqtinchalik**: har deploy/restartda SQLite bazasi (foydalanuvchilar, saralanganlar)
  o'chib ketishi mumkin. Doimiy saqlash uchun Persistent Disk (pullik) ulang va `DB_PATH=/data/music_bot.db` qiling.
- **YouTube/Instagram datacenter IP larni bloklashi mumkin.** Muammo bo'lsa admin paneldan
  «🔄 yt-dlp ni Yangilash», keyin kerak bo'lsa brauzerdan cookies.txt eksport qilib `COOKIES_FILE` ga ko'rsating.
- Telegram bot orqali yuboriladigan fayl limiti ~50 MB; foydalanuvchidan yuklab olish limiti 20 MB
  (shuning uchun Shazam/effektlar katta fayllarda ishlamaydi).
- Lyrics bepul `lyrics.ovh` API orqali olinadi — barcha qo'shiqlar topilmasligi mumkin.
- TikTok suv belgisiz yuklash `tikwm.com` ochiq API siga tayanadi (yt-dlp zaxira sifatida).
