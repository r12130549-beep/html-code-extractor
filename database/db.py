"""
Database layer using SQLite + aiosqlite.
Handles users, history, settings, and request statistics.
"""
import json
from datetime import datetime
from typing import Any

import aiosqlite

from config import DB_PATH, DEFAULT_SETTINGS, MAX_HISTORY_ENTRIES


# ─── Schema ─────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    joined_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    url         TEXT NOT NULL,
    filename    TEXT NOT NULL,
    file_size   INTEGER,
    status      TEXT NOT NULL,   -- 'success' | 'failed' | 'timeout'
    created_at  TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS settings (
    user_id             INTEGER PRIMARY KEY,
    output_filename     TEXT    NOT NULL DEFAULT 'extract.html',
    encoding            TEXT    NOT NULL DEFAULT 'utf-8',
    include_headers     INTEGER NOT NULL DEFAULT 0,
    beautify_html       INTEGER NOT NULL DEFAULT 0,
    auto_delete         INTEGER NOT NULL DEFAULT 1,
    timeout             INTEGER NOT NULL DEFAULT 30,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS stats (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO stats (key, value) VALUES
    ('total_users', 0),
    ('total_requests', 0),
    ('successful_extractions', 0),
    ('failed_requests', 0);
"""


async def init_db() -> None:
    """Initialise the database and create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


# ─── Users ──────────────────────────────────────────────────────────────────
async def upsert_user(user_id: int, username: str | None, first_name: str) -> bool:
    """Register or update a user atomically. Returns True if this is a new user."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Atomic insert-or-ignore followed by a conditional stats bump
        cursor = await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at) VALUES (?,?,?,?)",
            (user_id, username, first_name, datetime.now().isoformat()),
        )
        is_new = cursor.rowcount > 0
        if is_new:
            await db.execute(
                "UPDATE stats SET value = value + 1 WHERE key = 'total_users'"
            )
        else:
            await db.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id),
            )
        await db.commit()
    return is_new


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users ORDER BY joined_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


# ─── History ─────────────────────────────────────────────────────────────────
async def add_history(
    user_id: int,
    url: str,
    filename: str,
    file_size: int | None,
    status: str,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, url, filename, file_size, status, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (user_id, url, filename, file_size, status, datetime.now().isoformat()),
        )
        # Trim old entries
        await db.execute(
            "DELETE FROM history WHERE user_id = ? AND id NOT IN "
            "(SELECT id FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?)",
            (user_id, user_id, MAX_HISTORY_ENTRIES),
        )
        # Update global stats
        await db.execute(
            "UPDATE stats SET value = value + 1 WHERE key = 'total_requests'"
        )
        if status == "success":
            await db.execute(
                "UPDATE stats SET value = value + 1 WHERE key = 'successful_extractions'"
            )
        else:
            await db.execute(
                "UPDATE stats SET value = value + 1 WHERE key = 'failed_requests'"
            )
        await db.commit()


async def get_history(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def clear_history(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM history WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        return cursor.rowcount


# ─── Settings ────────────────────────────────────────────────────────────────
async def get_settings(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM settings WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return dict(DEFAULT_SETTINGS)
        data = dict(row)
        data["include_headers"] = bool(data["include_headers"])
        data["beautify_html"] = bool(data["beautify_html"])
        data["auto_delete"] = bool(data["auto_delete"])
        return data


async def upsert_settings(user_id: int, **kwargs: Any) -> None:
    """Create or update individual setting keys for a user."""
    current = await get_settings(user_id)
    current.update(kwargs)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings "
            "(user_id, output_filename, encoding, include_headers, beautify_html, auto_delete, timeout) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                user_id,
                current["output_filename"],
                current["encoding"],
                int(current["include_headers"]),
                int(current["beautify_html"]),
                int(current["auto_delete"]),
                int(current["timeout"]),
            ),
        )
        await db.commit()


# ─── Stats ───────────────────────────────────────────────────────────────────
async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT key, value FROM stats")
        rows = await cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}
