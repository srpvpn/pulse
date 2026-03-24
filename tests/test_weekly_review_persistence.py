def test_weekly_review_save_persists_latest_mbi_checkin(tmp_path):
    from pulse.db import Database

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_mbi_checkin("2026-03-23", 3, 2, 1)

    checkin = db.latest_mbi_checkin()

    assert checkin is not None
    assert checkin["exhaustion"] == 3
    assert checkin["cynicism"] == 2
    assert checkin["efficacy"] == 1


def test_save_weekly_checkin_upserts_mbi_note_and_recomputes_scores(tmp_path):
    from pulse.db import Database
    from pulse.ui.evening_input import HourlyEnergySample

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=[HourlyEnergySample(hour=8, level=4.0), HourlyEnergySample(hour=9, level=5.0)],
        sleep_hours=6.0,
        stress_level="high",
    )
    db.save_evening_input(
        date="2026-03-24",
        hourly_samples=[HourlyEnergySample(hour=8, level=6.0), HourlyEnergySample(hour=9, level=7.0)],
        sleep_hours=7.5,
        stress_level="low",
    )

    db.save_weekly_checkin(
        week="2026-03-23",
        exhaustion=3,
        cynicism=2,
        efficacy=1,
        note="Protect mornings next week",
    )

    with db.connect() as connection:
        mbi_row = connection.execute(
            "SELECT week, exhaustion, cynicism, efficacy FROM mbi_checkins"
        ).fetchone()
        note_row = connection.execute(
            "SELECT week, note FROM weekly_notes"
        ).fetchone()
        score_rows = connection.execute(
            "SELECT date, score, mbi_correction FROM burnout_scores ORDER BY date"
        ).fetchall()

    assert mbi_row["week"] == "2026-03-23"
    assert mbi_row["exhaustion"] == 3
    assert note_row["note"] == "Protect mornings next week"
    assert [row["date"] for row in score_rows] == ["2026-03-23", "2026-03-24"]
    assert all(row["score"] is not None for row in score_rows)
    assert all(row["mbi_correction"] < 0 for row in score_rows)
