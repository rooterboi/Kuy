"""Bot sozlamalari. Barcha qiymatlar .env / muhit o'zgaruvchilaridan o'qiladi."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _parse_ids(raw: str) -> list[int]:
    """'1, 2,3' -> [1, 2, 3]"""
    return [int(x) for x in raw.replace(" ", "").split(",") if x.lstrip("-").isdigit()]


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = _parse_ids(os.getenv("ADMIN_IDS", ""))

DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "music_bot.db"))
TMP_DIR: Path = Path(os.getenv("TMP_DIR", str(BASE_DIR / "tmp")))
LOG_FILE: Path = Path(os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "bot.log")))
COOKIES_FILE: str = os.getenv("COOKIES_FILE", "")  # Instagram/YouTube uchun (ixtiyoriy)

PORT: int = int(os.getenv("PORT", "10000"))  # Render health-check porti
MAX_FILE_MB: int = int(os.getenv("MAX_FILE_MB", "49"))  # Telegram bot limiti ~50 MB
MAX_FILE_BYTES: int = MAX_FILE_MB * 1024 * 1024
MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))  # bepul serverda xotira kam
SEARCH_RESULTS: int = int(os.getenv("SEARCH_RESULTS", "8"))

SUPPORTED_LANGS = ("uz", "ru", "en")
DEFAULT_LANG = "uz"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi! .env faylga yoki Render Environment ga qo'shing.")

for _d in (TMP_DIR, LOG_FILE.parent, Path(DB_PATH).parent):
    _d.mkdir(parents=True, exist_ok=True)
