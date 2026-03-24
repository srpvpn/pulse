"""SQLite storage helpers for Pulse."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Union

from pulse.burnout_engine import BurnoutEntry, compute_burnout_score
from pulse.ui.weekly_review import MBICheckin, compute_mbi_correction


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
        week TEXT NOT NULL UNIQUE,
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
    """
    CREATE TABLE IF NOT EXISTS ritual_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        ritual_id TEXT NOT NULL,
        delivered_time TEXT NOT NULL,
        created TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, ritual_id)
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
            self._migrate_schema(connection)

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

    def save_ritual(
        self,
        ritual_id: str,
        label: str,
        time: str,
        active: bool = True,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO rituals (ritual_id, label, time, active)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ritual_id) DO UPDATE SET
                    label = excluded.label,
                    time = excluded.time,
                    active = excluded.active
                """,
                (ritual_id, label, time, 1 if active else 0),
            )

    def list_rituals(self) -> List[sqlite3.Row]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT ritual_id, label, time, active
                FROM rituals
                ORDER BY time, label
                """
            ).fetchall()
        return rows

    def list_active_rituals(self) -> List[sqlite3.Row]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT ritual_id, label, time, active
                FROM rituals
                WHERE active = 1
                ORDER BY time, label
                """
            ).fetchall()
        return rows

    def save_mbi_checkin(
        self,
        current_date: str,
        exhaustion: int,
        cynicism: int,
        efficacy: int,
    ) -> None:
        self.save_weekly_checkin(
            week=current_date,
            exhaustion=exhaustion,
            cynicism=cynicism,
            efficacy=efficacy,
            note="",
        )

    def save_weekly_checkin(
        self,
        week: str,
        exhaustion: int,
        cynicism: int,
        efficacy: int,
        note: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO mbi_checkins (week, exhaustion, cynicism, efficacy)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(week) DO UPDATE SET
                    exhaustion = excluded.exhaustion,
                    cynicism = excluded.cynicism,
                    efficacy = excluded.efficacy
                """,
                (
                    week,
                    int(exhaustion),
                    int(cynicism),
                    int(efficacy),
                ),
            )
            connection.execute(
                """
                INSERT INTO weekly_notes (week, note)
                VALUES (?, ?)
                ON CONFLICT(week) DO UPDATE SET
                    note = excluded.note
                """,
                (week, note),
            )
            self._recompute_burnout_scores(connection, start_date=week)

    def latest_mbi_checkin(self) -> Optional[sqlite3.Row]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT week, exhaustion, cynicism, efficacy
                FROM mbi_checkins
                ORDER BY week DESC
                LIMIT 1
                """
            ).fetchone()
        return row

    def weekly_note_for_week(self, week: str) -> Optional[str]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT note
                FROM weekly_notes
                WHERE week = ?
                """,
                (week,),
            ).fetchone()
        return None if row is None else row["note"]

    def mark_ritual_delivered(
        self,
        current_date: str,
        ritual_id: str,
        delivered_time: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO ritual_deliveries (date, ritual_id, delivered_time)
                VALUES (?, ?, ?)
                ON CONFLICT(date, ritual_id) DO UPDATE SET
                    delivered_time = excluded.delivered_time
                """,
                (current_date, ritual_id, delivered_time),
            )

    def list_delivered_ritual_ids(self, current_date: str) -> List[str]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT ritual_id
                FROM ritual_deliveries
                WHERE date = ?
                ORDER BY delivered_time, ritual_id
                """,
                (current_date,),
            ).fetchall()
        return [row["ritual_id"] for row in rows]

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
            self._recompute_burnout_scores(connection)

    def _migrate_schema(self, connection: sqlite3.Connection) -> None:
        mbi_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(mbi_checkins)").fetchall()
        }
        if "week" not in mbi_columns and "date" in mbi_columns:
            self._rebuild_mbi_checkins_table(connection)
            return

        if "date" in mbi_columns:
            date_column = next(
                row
                for row in connection.execute("PRAGMA table_info(mbi_checkins)").fetchall()
                if row["name"] == "date"
            )
            if int(date_column["notnull"]) == 1:
                self._rebuild_mbi_checkins_table(connection)

    def _rebuild_mbi_checkins_table(self, connection: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(mbi_checkins)").fetchall()
        }
        source_week_expression = "COALESCE(week, date)" if "week" in existing_columns else "date"
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mbi_checkins_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week TEXT NOT NULL UNIQUE,
                exhaustion INTEGER NOT NULL,
                cynicism INTEGER NOT NULL,
                efficacy INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO mbi_checkins_new (id, week, exhaustion, cynicism, efficacy)
            SELECT id,
                   {source_week_expression},
                   exhaustion,
                   cynicism,
                   efficacy
            FROM mbi_checkins
            """.format(source_week_expression=source_week_expression)
        )
        connection.execute("DROP TABLE mbi_checkins")
        connection.execute("ALTER TABLE mbi_checkins_new RENAME TO mbi_checkins")
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_mbi_checkins_week
            ON mbi_checkins(week)
            """
        )

    def _recompute_burnout_scores(
        self,
        connection: sqlite3.Connection,
        start_date: Optional[str] = None,
    ) -> None:
        rows = connection.execute(
            """
            SELECT e.date AS date,
                   AVG(e.level) AS average_energy,
                   c.sleep_hours AS sleep_hours,
                   c.stress_level AS stress_level,
                   c.physical_activity AS physical_activity
            FROM energy_logs e
            LEFT JOIN daily_context c ON c.date = e.date
            GROUP BY e.date
            ORDER BY e.date
            """
        ).fetchall()
        if not rows:
            connection.execute("DELETE FROM burnout_scores")
            return

        entries = [
            BurnoutEntry(
                date=row["date"],
                average_energy=float(row["average_energy"]),
                sleep_hours=row["sleep_hours"],
                stress_level=row["stress_level"],
                physical_activity=row["physical_activity"],
            )
            for row in rows
        ]
        corrections = self._load_mbi_corrections_by_week(connection)

        for index, entry in enumerate(entries, start=1):
            if start_date is not None and entry.date < start_date:
                continue
            correction = _mbi_correction_for_date(entry.date, corrections)
            result = compute_burnout_score(entries[:index], mbi_correction=correction)
            connection.execute(
                """
                INSERT INTO burnout_scores (date, score, ali, rqs, trend_penalty, mbi_correction)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    score = excluded.score,
                    ali = excluded.ali,
                    rqs = excluded.rqs,
                    trend_penalty = excluded.trend_penalty,
                    mbi_correction = excluded.mbi_correction
                """,
                (
                    entry.date,
                    result.score,
                    result.ali,
                    result.rqs,
                    result.trend_penalty,
                    result.mbi_correction,
                ),
            )

        if start_date is not None:
            connection.execute(
                """
                DELETE FROM burnout_scores
                WHERE date >= ?
                  AND date NOT IN (
                      SELECT DISTINCT date FROM energy_logs
                  )
                """,
                (start_date,),
            )

    def _load_mbi_corrections_by_week(self, connection: sqlite3.Connection):
        rows = connection.execute(
            """
            SELECT week, exhaustion, cynicism, efficacy
            FROM mbi_checkins
            WHERE week IS NOT NULL
            ORDER BY week
            """
        ).fetchall()
        return [
            (
                row["week"],
                compute_mbi_correction(
                    MBICheckin(
                        exhaustion=int(row["exhaustion"]),
                        cynicism=int(row["cynicism"]),
                        efficacy=int(row["efficacy"]),
                    )
                ),
            )
            for row in rows
        ]


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


def _mbi_correction_for_date(date_text: str, corrections_by_week) -> float:
    current_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    latest = 0.0
    for week_text, correction in corrections_by_week:
        week_date = datetime.strptime(week_text, "%Y-%m-%d").date()
        if week_date <= current_date:
            latest = correction
            continue
        break
    return latest
