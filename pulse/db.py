"""SQLite storage helpers for Pulse."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Union


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

    def save_evening_input(
        self,
        date: str,
        hourly_samples: Iterable[object],
        sleep_hours: Optional[float] = None,
        physical_activity: Optional[str] = None,
        stress_level: Optional[str] = None,
        free_note: Optional[str] = None,
    ) -> None:
        rows = _dedupe_hourly_samples(hourly_samples)
        with self.connect() as connection:
            connection.execute("DELETE FROM energy_logs WHERE date = ?", (date,))
            connection.executemany(
                """
                INSERT INTO energy_logs (date, hour, level)
                VALUES (?, ?, ?)
                """,
                [(date, sample.hour, sample.level) for sample in rows],
            )
            connection.execute(
                """
                INSERT INTO daily_context (
                    date,
                    sleep_hours,
                    physical_activity,
                    stress_level,
                    free_note
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    sleep_hours = excluded.sleep_hours,
                    physical_activity = excluded.physical_activity,
                    stress_level = excluded.stress_level,
                    free_note = excluded.free_note
                """,
                (date, sleep_hours, physical_activity, stress_level, free_note),
            )


def _dedupe_hourly_samples(hourly_samples: Iterable[object]) -> List[object]:
    samples_by_hour = {}
    for sample in hourly_samples:
        hour = _clamp_hour(sample.hour)
        level = _clamp_level(sample.level)
        samples_by_hour[hour] = _StoredHourlySample(hour=hour, level=level)
    return [samples_by_hour[hour] for hour in sorted(samples_by_hour)]


class _StoredHourlySample(object):
    def __init__(self, hour: int, level: float) -> None:
        self.hour = hour
        self.level = level


def _clamp_hour(value: object) -> int:
    try:
        hour = int(value)
    except (TypeError, ValueError):
        hour = 8
    return max(8, min(23, hour))


def _clamp_level(value: object) -> float:
    try:
        level = float(value)
    except (TypeError, ValueError):
        level = 1.0
    return max(1.0, min(10.0, level))
