"""SQLite bilan ishlash qatlami (stdlib sqlite3 + asyncio.to_thread)."""
import asyncio
import sqlite3
from typing import Any, Optional

from database.schema import SCHEMA


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()

    # ---------------------------------------------------------- core
    async def connect(self) -> None:
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.execute("DELETE FROM links WHERE created_at < datetime('now','-7 days')")
        self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            self._conn.close()

    def _sync(self, sql: str, params: tuple, fetch: str) -> Any:
        cur = self._conn.execute(sql, params)
        if fetch == "one":
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetch == "all":
            result = [dict(r) for r in cur.fetchall()]
        elif fetch == "scalar":
            row = cur.fetchone()
            result = row[0] if row else None
        elif fetch == "lastrowid":
            result = cur.lastrowid
        else:
            result = cur.rowcount
        self._conn.commit()
        return result

    async def _q(self, sql: str, params: tuple = (), fetch: str = "none") -> Any:
        async with self._lock:
            return await asyncio.to_thread(self._sync, sql, params, fetch)

    # ---------------------------------------------------------- users
    async def upsert_user(self, user_id: int, username: Optional[str], full_name: str) -> None:
        await self._q(
            "INSERT INTO users(user_id, username, full_name) VALUES(?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, "
            "full_name=excluded.full_name, last_active=datetime('now')",
            (user_id, username, full_name),
        )

    async def get_user(self, user_id: int) -> Optional[dict]:
        return await self._q("SELECT * FROM users WHERE user_id=?", (user_id,), "one")

    async def set_lang(self, user_id: int, lang: str) -> None:
        await self._q("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))

    async def set_ban(self, user_id: int, banned: bool) -> int:
        return await self._q("UPDATE users SET is_banned=? WHERE user_id=?", (int(banned), user_id))

    async def all_user_ids(self) -> list[int]:
        rows = await self._q("SELECT user_id FROM users WHERE is_banned=0", (), "all")
        return [r["user_id"] for r in rows]

    # ---------------------------------------------------------- tracks
    async def upsert_track(self, video_id: str, title: str, artist: str, duration: int) -> int:
        await self._q(
            "INSERT INTO tracks(video_id, title, artist, duration) VALUES(?,?,?,?) "
            "ON CONFLICT(video_id) DO UPDATE SET title=excluded.title, "
            "artist=excluded.artist, duration=excluded.duration",
            (video_id, title, artist, duration),
        )
        return await self._q("SELECT id FROM tracks WHERE video_id=?", (video_id,), "scalar")

    async def set_track_file(self, track_id: int, file_id: str) -> None:
        await self._q("UPDATE tracks SET file_id=? WHERE id=?", (file_id, track_id))

    async def get_track(self, track_id: int) -> Optional[dict]:
        return await self._q("SELECT * FROM tracks WHERE id=?", (track_id,), "one")

    async def get_track_by_video(self, video_id: str) -> Optional[dict]:
        return await self._q("SELECT * FROM tracks WHERE video_id=?", (video_id,), "one")

    async def inc_plays(self, track_id: int) -> None:
        await self._q("UPDATE tracks SET plays=plays+1 WHERE id=?", (track_id,))

    async def top_tracks(self, limit: int = 10) -> list[dict]:
        return await self._q(
            "SELECT * FROM tracks WHERE plays>0 ORDER BY plays DESC, id DESC LIMIT ?", (limit,), "all"
        )

    # ---------------------------------------------------------- search log
    async def log_search(self, query: str) -> None:
        await self._q(
            "INSERT INTO search_log(query) VALUES(?) "
            "ON CONFLICT(query) DO UPDATE SET hits=hits+1, last_at=datetime('now')",
            (query.lower(),),
        )

    # ---------------------------------------------------------- favorites
    async def add_favorite(self, user_id: int, track_id: int) -> bool:
        n = await self._q("INSERT OR IGNORE INTO favorites(user_id, track_id) VALUES(?,?)", (user_id, track_id))
        return n > 0

    async def remove_favorite(self, user_id: int, track_id: int) -> None:
        await self._q("DELETE FROM favorites WHERE user_id=? AND track_id=?", (user_id, track_id))

    async def list_favorites(self, user_id: int) -> list[dict]:
        return await self._q(
            "SELECT t.id, t.title, t.artist FROM favorites f JOIN tracks t ON t.id=f.track_id "
            "WHERE f.user_id=? ORDER BY f.added_at DESC LIMIT 40",
            (user_id,),
            "all",
        )

    # ---------------------------------------------------------- channels
    async def add_channel(self, chat_id: int, title: str, url: str) -> None:
        await self._q(
            "INSERT INTO channels(chat_id, title, url) VALUES(?,?,?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title, url=excluded.url",
            (chat_id, title, url),
        )

    async def remove_channel(self, chat_id: int) -> None:
        await self._q("DELETE FROM channels WHERE chat_id=?", (chat_id,))

    async def list_channels(self) -> list[dict]:
        return await self._q("SELECT * FROM channels", (), "all")

    # ---------------------------------------------------------- links
    async def save_link(self, url: str) -> int:
        return await self._q("INSERT INTO links(url) VALUES(?)", (url,), "lastrowid")

    async def get_link(self, link_id: int) -> Optional[str]:
        return await self._q("SELECT url FROM links WHERE id=?", (link_id,), "scalar")

    # ---------------------------------------------------------- stats
    async def get_stats(self) -> dict:
        return {
            "users": await self._q("SELECT COUNT(*) FROM users", (), "scalar"),
            "active_today": await self._q(
                "SELECT COUNT(*) FROM users WHERE date(last_active)=date('now')", (), "scalar"
            ),
            "banned": await self._q("SELECT COUNT(*) FROM users WHERE is_banned=1", (), "scalar"),
            "tracks": await self._q("SELECT COUNT(*) FROM tracks", (), "scalar"),
            "top_tracks": await self.top_tracks(5),
            "top_queries": await self._q(
                "SELECT query, hits FROM search_log ORDER BY hits DESC LIMIT 5", (), "all"
            ),
        }
