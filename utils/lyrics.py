"""Qo'shiq matnini topish (bepul lyrics.ovh API, kalitsiz)."""
import re
from typing import Optional
from urllib.parse import quote

import aiohttp

from utils.logger import get_logger

log = get_logger(__name__)

_NOISE = re.compile(
    r"[\(\[](official|lyrics?|lyric video|video|audio|hd|4k|hq|mv|clip|music video|клип|премьера)[^\)\]]*[\)\]]",
    re.I,
)


def split_artist_title(title: str, uploader: str) -> tuple[str, str]:
    """YouTube sarlavhasidan (Artist - Qo'shiq) ni ajratadi."""
    clean = re.sub(r"\s+", " ", _NOISE.sub("", title)).strip(" -|")
    for sep in (" - ", " – ", " — ", " | "):
        if sep in clean:
            artist, song = clean.split(sep, 1)
            return artist.strip(), song.strip()
    artist = re.sub(r"(?i)\s*-\s*topic$", "", uploader or "").strip()
    return artist, clean


async def _ovh(session: aiohttp.ClientSession, artist: str, song: str) -> Optional[str]:
    url = f"https://api.lyrics.ovh/v1/{quote(artist, safe='')}/{quote(song, safe='')}"
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json(content_type=None)
            return (data.get("lyrics") or "").strip() or None
    except Exception as exc:
        log.warning("lyrics.ovh xatosi: %s", exc)
        return None


async def fetch_lyrics(title: str, uploader: str = "") -> Optional[str]:
    artist, song = split_artist_title(title, uploader)
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        text = await _ovh(session, artist, song)
        if text:
            return text
        # Zaxira: suggest orqali eng mos juftlikni qidiramiz
        try:
            async with session.get(f"https://api.lyrics.ovh/suggest/{quote(f'{artist} {song}'.strip())}") as resp:
                data = (await resp.json(content_type=None)).get("data") or []
        except Exception:
            return None
        for item in data[:3]:
            text = await _ovh(session, item["artist"]["name"], item["title"])
            if text:
                return text
    return None
