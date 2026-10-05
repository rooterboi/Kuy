"""SQLite jadvallari sxemasi."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    lang        TEXT,
    is_banned   INTEGER NOT NULL DEFAULT 0,
    joined_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_active TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tracks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id   TEXT UNIQUE NOT NULL,
    title      TEXT NOT NULL,
    artist     TEXT DEFAULT '',
    duration   INTEGER DEFAULT 0,
    file_id    TEXT,
    plays      INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id  INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    added_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, track_id)
);

CREATE TABLE IF NOT EXISTS channels (
    chat_id INTEGER PRIMARY KEY,
    title   TEXT NOT NULL,
    url     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS links (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    url        TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS search_log (
    query   TEXT PRIMARY KEY,
    hits    INTEGER NOT NULL DEFAULT 1,
    last_at TEXT DEFAULT (datetime('now'))
);
"""
