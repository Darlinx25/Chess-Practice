"""SQLite storage for training progress."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Optional

from app.config import DATA_DIR, DB_PATH, total_exercises

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total INTEGER NOT NULL,
    solved INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_number INTEGER NOT NULL,
    cycle INTEGER NOT NULL,
    session_id INTEGER,
    solved INTEGER NOT NULL,
    time_ms INTEGER NOT NULL,
    ts TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_attempts_ex ON attempts(exercise_number);
CREATE INDEX IF NOT EXISTS idx_attempts_cyc ON attempts(cycle);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with _connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def create_session(cycle: int, session_number: int, total: int) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO sessions(cycle, session_number, started_at, total) "
            "VALUES(?, ?, ?, ?)",
            (cycle, session_number, datetime.now().isoformat(timespec="seconds"), total),
        )
        return int(cur.lastrowid)


def finish_session(session_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE sessions SET finished_at=? WHERE id=?",
            (datetime.now().isoformat(timespec="seconds"), session_id),
        )


def record_attempt(exercise_number: int, cycle: int, session_id: int,
                   solved: bool, time_ms: int) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO attempts(exercise_number, cycle, session_id, solved, time_ms, ts) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (exercise_number, cycle, session_id, int(solved), int(time_ms),
             datetime.now().isoformat(timespec="seconds")),
        )
        if solved:
            conn.execute(
                "UPDATE sessions SET solved = solved + 1 WHERE id=?", (session_id,)
            )


def exercise_stats(number: int) -> dict:
    """Accuracy and attempt history for one exercise."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT solved, time_ms, ts FROM attempts WHERE exercise_number=? "
            "ORDER BY ts", (number,)).fetchall()
        all_rows = conn.execute(
            "SELECT exercise_number, solved FROM attempts "
            "WHERE exercise_number=? AND solved=0", (number,)).fetchall()
    if not rows:
        return {"attempts": 0, "solved": 0, "misses": 0, "accuracy": 0.0,
                "avg_time_ms": 0, "last_ts": None}
    solves = sum(1 for r in rows if r["solved"])
    return {
        "attempts": len(rows),
        "solved": solves,
        "misses": len(all_rows),
        "accuracy": solves / len(rows),
        "avg_time_ms": int(sum(r["time_ms"] for r in rows) / len(rows)),
        "last_ts": rows[-1]["ts"],
    }


def overall_progress() -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT exercise_number) AS n, "
            "COUNT(*) AS total, SUM(solved) AS solved "
            "FROM attempts").fetchone()
        sessions = conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()
    return {"unique_solved": row["n"] or 0, "total_attempts": row["total"] or 0,
            "solved": row["solved"] or 0, "sessions": sessions["n"] or 0}


def cycle_summary(cycle: int) -> dict:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT exercise_number, solved, ts FROM attempts WHERE cycle=?",
            (cycle,)).fetchall()
    done = {r["exercise_number"] for r in rows if r["solved"]}
    return {"cycle": cycle, "done": len(done), "total": total_exercises(),
            "attempts": len(rows)}


def solved_numbers_in_cycle(cycle: int) -> list[int]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT exercise_number FROM attempts "
            "WHERE cycle=? AND solved=1", (cycle,)).fetchall()
    return [r["exercise_number"] for r in rows]


def reset_all() -> None:
    """Delete all training data and settings (fresh start)."""
    with _connect() as conn:
        conn.execute("DELETE FROM attempts")
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM settings")
