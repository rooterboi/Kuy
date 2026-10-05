"""Kichik yordamchi funksiyalar."""
import html
from pathlib import Path
from typing import Optional


def esc(text) -> str:
    """HTML-xavfsiz matn."""
    return html.escape(str(text or ""))


def fmt_duration(seconds: int) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


def split_text(text: str, size: int = 3800) -> list[str]:
    """Uzun matnni Telegram limitiga (4096) mos bo'laklarga bo'ladi."""
    chunks, current = [], ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > size:
            chunks.append(current)
            current = ""
        current += line
    if current.strip():
        chunks.append(current)
    return chunks


def safe_remove(*paths: Optional[Path]) -> None:
    for p in paths:
        try:
            if p:
                Path(p).unlink(missing_ok=True)
        except OSError:
            pass


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"
