def test_initialize_creates_required_tables(tmp_path):
    from pulse.db import Database

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    assert set(db.list_tables()) >= {
        "energy_logs",
        "daily_context",
        "mbi_checkins",
        "burnout_scores",
        "rituals",
        "weekly_notes",
    }


def test_initialize_migrates_legacy_mbi_checkins_table_to_week_schema(tmp_path):
    import sqlite3

    from pulse.db import Database

    db_path = tmp_path / "pulse.db"
    connection = sqlite3.connect(str(db_path))
    connection.execute(
        """
        CREATE TABLE mbi_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            exhaustion INTEGER NOT NULL,
            cynicism INTEGER NOT NULL,
            efficacy INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO mbi_checkins (date, exhaustion, cynicism, efficacy)
        VALUES ('2026-03-23', 3, 2, 1)
        """
    )
    connection.commit()
    connection.close()

    db = Database(db_path)
    db.initialize()
    db.save_weekly_checkin(
        week="2026-03-30",
        exhaustion=1,
        cynicism=1,
        efficacy=3,
        note="lighter load",
    )

    with db.connect() as connection:
        columns = connection.execute("PRAGMA table_info(mbi_checkins)").fetchall()
        rows = connection.execute(
            "SELECT week, exhaustion, cynicism, efficacy FROM mbi_checkins ORDER BY week"
        ).fetchall()

    assert {row["name"] for row in columns} == {"id", "week", "exhaustion", "cynicism", "efficacy"}
    assert [row["week"] for row in rows] == ["2026-03-23", "2026-03-30"]
