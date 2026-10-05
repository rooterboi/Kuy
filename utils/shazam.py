"""Shazam orqali musiqani aniqlash (shazamio, API kalitsiz)."""
import asyncio
from dataclasses import dataclass
from typing import Optional

from shazamio import Shazam


@dataclass
class Recognized:
    title: str
    artist: str
    cover: Optional[str]


async def recognize(path: str) -> Optional[Recognized]:
    shazam = Shazam()
    # shazamio versiyalariga moslik: yangisida recognize, eskisida recognize_song
    func = getattr(shazam, "recognize", None) or getattr(shazam, "recognize_song")
    out = await asyncio.wait_for(func(path), timeout=90)
    track = (out or {}).get("track")
    if not track:
        return None
    return Recognized(
        title=track.get("title", ""),
        artist=track.get("subtitle", ""),
        cover=(track.get("images") or {}).get("coverart"),
    )
