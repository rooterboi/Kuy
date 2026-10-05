"""FFmpeg audio effektlari: tezlashtirish, sekinlashtirish, BASS Boost, 8D."""
import asyncio
from pathlib import Path

from pydub.utils import mediainfo

# effekt kodi -> ffmpeg audio filtri
FILTERS: dict[str, str] = {
    "s125": "atempo=1.25",
    "s150": "atempo=1.5",
    "slow": "atempo=0.8",
    "bass": "bass=g=15:f=110:w=0.6,alimiter=limit=0.95",
    "8d": "apulsator=mode=sine:hz=0.125:amount=1",  # chap-o'ng aylanuvchi tovush
}
LABELS: dict[str, str] = {
    "s125": "1.25x", "s150": "1.5x", "slow": "0.8x", "bass": "BASS", "8d": "8D",
}


class EffectError(Exception):
    pass


async def apply_effect(src: Path, dst: Path, mode: str, timeout: int = 240) -> None:
    if mode not in FILTERS:
        raise EffectError(f"Noma'lum effekt: {mode}")
    cmd = [
        "ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "2",
        "-af", FILTERS[mode], "-codec:a", "libmp3lame", "-b:a", "192k", str(dst),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
    )
    try:
        _, err = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise EffectError("FFmpeg timeout")
    if proc.returncode != 0:
        raise EffectError(err.decode(errors="ignore")[-500:])


async def get_duration(path: Path) -> int:
    """Audio davomiyligi (soniya). pydub orqali ffprobe ishlatiladi."""
    try:
        info = await asyncio.to_thread(mediainfo, str(path))
        return int(float(info.get("duration", 0)))
    except Exception:
        return 0
