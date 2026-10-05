"""Tizim yordamchilari: yt-dlp yangilash, kesh tozalash, restart, resurs monitoring."""
import asyncio
import importlib.metadata
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Optional

from config import BASE_DIR, LOG_FILE, TMP_DIR

START_TIME = time.time()


# ------------------------------------------------------------------ jarayonlar
async def run_cmd(*args: str, timeout: int = 300) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Timeout"
    return proc.returncode or 0, out.decode(errors="ignore")


async def update_ytdlp() -> tuple[bool, str]:
    """pip install --upgrade yt-dlp"""
    code, out = await run_cmd(sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "yt-dlp")
    return code == 0, out[-800:]


def get_ytdlp_version() -> str:
    try:
        return importlib.metadata.version("yt-dlp")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def restart_bot() -> None:
    """Jarayonni o'z o'rnida qayta ishga tushiradi (Docker ichida PID o'zgarmaydi)."""
    logging.shutdown()
    os.execv(sys.executable, [sys.executable, *sys.argv])


# ------------------------------------------------------------------ kesh / disk
def clean_tmp(older_than_sec: int = 0) -> tuple[int, int]:
    """TMP_DIR ni tozalaydi. (o'chirilgan fayllar soni, bo'shatilgan bayt) qaytaradi."""
    count, freed, now = 0, 0, time.time()
    for p in TMP_DIR.glob("*"):
        try:
            if p.is_file() and (now - p.stat().st_mtime) >= older_than_sec:
                freed += p.stat().st_size
                p.unlink()
                count += 1
        except OSError:
            continue
    return count, freed


def tmp_size() -> int:
    return sum(p.stat().st_size for p in TMP_DIR.glob("*") if p.is_file())


def disk_info() -> tuple[int, int, int]:
    total, used, free = shutil.disk_usage(BASE_DIR)
    return total, used, free


def memory_info() -> Optional[tuple[int, int]]:
    """(jami, ishlatilgan) bayt. Avval cgroup (Docker limiti), keyin /proc/meminfo."""
    try:
        limit_raw = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if limit_raw != "max":
            used = int(Path("/sys/fs/cgroup/memory.current").read_text())
            return int(limit_raw), used
    except Exception:
        pass
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            info[k] = int(v.strip().split()[0]) * 1024
        return info["MemTotal"], info["MemTotal"] - info["MemAvailable"]
    except Exception:
        return None


def uptime_str() -> str:
    s = int(time.time() - START_TIME)
    return f"{s // 3600}s {s % 3600 // 60}d"


# ------------------------------------------------------------------ log fayl
def log_tail(lines: int = 30) -> str:
    try:
        content = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(content[-lines:])
    except FileNotFoundError:
        return ""


def clear_log() -> None:
    with open(LOG_FILE, "w", encoding="utf-8"):
        pass
