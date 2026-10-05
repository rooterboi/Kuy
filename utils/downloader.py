"""yt-dlp asosidagi qidiruv va yuklash (YouTube, Instagram, TikTok, Pinterest)."""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp
from yt_dlp import YoutubeDL

from config import COOKIES_FILE, MAX_CONCURRENT_JOBS, MAX_FILE_BYTES, TMP_DIR
from utils.logger import get_logger

log = get_logger(__name__)

# Og'ir ishlar (yuklash, FFmpeg) bir vaqtda ko'p bo'lmasligi uchun (bepul serverda RAM kam)
JOB_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_JOBS)

# HD dan boshlab, fayl katta bo'lsa pastroq sifatga tushadi
VIDEO_FORMATS = [
    "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/bv*[height<=720]+ba/b[height<=720]/b",
    "b[height<=480]/bv*[height<=480]+ba/b",
    "b[height<=360]/worst",
]


class DownloadError(Exception):
    pass


class FileTooBigError(DownloadError):
    pass


@dataclass
class MediaInfo:
    path: Path
    title: str
    uploader: str
    duration: int
    width: Optional[int]
    height: Optional[int]
    video_id: str


# ------------------------------------------------------------------ yordamchilar
def _base_opts(uid: str) -> dict:
    opts = {
        "outtmpl": str(TMP_DIR / f"{uid}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "retries": 3,
        "restrictfilenames": True,
    }
    if COOKIES_FILE and Path(COOKIES_FILE).exists():
        opts["cookiefile"] = COOKIES_FILE
    return opts


def _cleanup_uid(uid: str) -> None:
    for p in TMP_DIR.glob(f"{uid}*"):
        try:
            p.unlink()
        except OSError:
            pass


def _find_output(uid: str) -> Optional[Path]:
    for p in TMP_DIR.glob(f"{uid}.*"):
        if p.suffix not in (".part", ".ytdl", ".temp"):
            return p
    return None


def _to_info(path: Path, info: dict) -> MediaInfo:
    if info and "entries" in info:
        info = (info["entries"] or [{}])[0]
    info = info or {}
    return MediaInfo(
        path=path,
        title=info.get("track") or info.get("title") or "Unknown",
        uploader=info.get("artist") or info.get("uploader") or info.get("channel") or "",
        duration=int(info.get("duration") or 0),
        width=info.get("width"),
        height=info.get("height"),
        video_id=info.get("id") or "",
    )


# ------------------------------------------------------------------ qidiruv
def _search_sync(query: str, limit: int) -> list[dict]:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True, "socket_timeout": 20}
    if COOKIES_FILE and Path(COOKIES_FILE).exists():
        opts["cookiefile"] = COOKIES_FILE
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit * 2}:{query}", download=False)

    items = []
    for e in (info or {}).get("entries") or []:
        if not e or not e.get("id"):
            continue
        duration = int(e.get("duration") or 0)
        if duration and not (30 <= duration <= 900):  # juda qisqa/uzun (mix) videolarni tashlaymiz
            continue
        items.append({
            "id": e["id"],
            "title": e.get("title") or "Unknown",
            "uploader": e.get("uploader") or e.get("channel") or "",
            "duration": duration,
            "views": int(e.get("view_count") or 0),
        })
    items.sort(key=lambda x: x["views"], reverse=True)  # eng ko'p eshitilganlar birinchi
    return items[:limit]


async def search_youtube(query: str, limit: int = 8) -> list[dict]:
    return await asyncio.to_thread(_search_sync, query, limit)


# ------------------------------------------------------------------ audio
def _audio_sync(url: str, uid: str) -> MediaInfo:
    opts = {
        **_base_opts(uid),
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    path = TMP_DIR / f"{uid}.mp3"
    if not path.exists():
        raise DownloadError("MP3 fayl yaratilmadi")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise FileTooBigError(str(path.stat().st_size))
    return _to_info(path, info)


async def download_audio(url: str) -> MediaInfo:
    uid = uuid.uuid4().hex
    try:
        return await asyncio.to_thread(_audio_sync, url, uid)
    except FileTooBigError:
        _cleanup_uid(uid)
        raise
    except Exception as exc:
        _cleanup_uid(uid)
        if "tiktok.com" in url.lower():
            log.warning("TikTok audio: yt-dlp xato berdi, tikwm zaxirasi: %s", exc)
            return await _tiktok_audio(url, uid)
        raise


# ------------------------------------------------------------------ video
def _video_sync(url: str, uid: str) -> MediaInfo:
    last_info: dict = {}
    for fmt in VIDEO_FORMATS:
        _cleanup_uid(uid)
        opts = {**_base_opts(uid), "format": fmt, "merge_output_format": "mp4"}
        with YoutubeDL(opts) as ydl:
            last_info = ydl.extract_info(url, download=True)
        path = _find_output(uid)
        if not path:
            raise DownloadError("Video fayl yaratilmadi")
        if path.stat().st_size <= MAX_FILE_BYTES:
            return _to_info(path, last_info)
    raise FileTooBigError("video > limit")


async def download_video(url: str) -> MediaInfo:
    uid = uuid.uuid4().hex
    if "tiktok.com" in url.lower():
        try:
            return await _tiktok_video(url, uid)  # suv belgisiz
        except FileTooBigError:
            _cleanup_uid(uid)
            raise
        except Exception as exc:
            log.warning("TikTok tikwm xatosi, yt-dlp ga o'tilmoqda: %s", exc)
            _cleanup_uid(uid)
    try:
        return await asyncio.to_thread(_video_sync, url, uid)
    except Exception:
        _cleanup_uid(uid)
        raise


# ------------------------------------------------------------------ TikTok (watermark-less)
async def _tikwm_data(url: str) -> dict:
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("https://www.tikwm.com/api/", params={"url": url, "hd": 1}) as resp:
            payload = await resp.json(content_type=None)
    if payload.get("code") != 0 or not payload.get("data"):
        raise DownloadError(f"tikwm: {payload.get('msg')}")
    return payload["data"]


async def _fetch_file(url: str, dest: Path) -> None:
    if url.startswith("/"):
        url = "https://www.tikwm.com" + url
    timeout = aiohttp.ClientTimeout(total=180)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in resp.content.iter_chunked(256 * 1024):
                    f.write(chunk)


async def _tiktok_video(url: str, uid: str) -> MediaInfo:
    data = await _tikwm_data(url)
    dest = TMP_DIR / f"{uid}.mp4"
    for key in ("hdplay", "play"):
        link = data.get(key)
        if not link:
            continue
        await _fetch_file(link, dest)
        if dest.stat().st_size <= MAX_FILE_BYTES:
            return MediaInfo(
                path=dest,
                title=data.get("title") or "TikTok",
                uploader=(data.get("author") or {}).get("nickname", ""),
                duration=int(data.get("duration") or 0),
                width=None, height=None, video_id=str(data.get("id", "")),
            )
    raise FileTooBigError("tiktok video > limit")


async def _tiktok_audio(url: str, uid: str) -> MediaInfo:
    data = await _tikwm_data(url)
    link = data.get("music")
    if not link:
        raise DownloadError("tikwm: music topilmadi")
    dest = TMP_DIR / f"{uid}.mp3"
    await _fetch_file(link, dest)
    return MediaInfo(
        path=dest,
        title=(data.get("music_info") or {}).get("title") or data.get("title") or "TikTok audio",
        uploader=(data.get("music_info") or {}).get("author", ""),
        duration=int(data.get("duration") or 0),
        width=None, height=None, video_id=str(data.get("id", "")),
    )
