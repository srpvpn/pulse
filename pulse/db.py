"""SQLite storage helpers for Pulse."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Union


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS energy_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        hour INTEGER NOT NULL,
        level REAL NOT NULL,
        note TEXT,
        created TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_context (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        sleep_hours REAL,
        physical_activity TEXT,
        stress_level TEXT,
        free_note TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mbi_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        exhaustion INTEGER NOT NULL,
        cynicism INTEGER NOT NULL,
        efficacy INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS burnout_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        score REAL NOT NULL,
        ali REAL NOT NULL,
        rqs REAL NOT NULL,
        trend_penalty REAL NOT NULL,
        mbi_correction REAL NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rituals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ritual_id TEXT NOT NULL UNIQUE,
        label TEXT NOT NULL,
        time TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS weekly_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week TEXT NOT NULL UNIQUE,
        note TEXT
    )
    """,
)


class Database:
    """Thin SQLite repository for Pulse."""

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)

    def list_tables(self) -> List[str]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]
