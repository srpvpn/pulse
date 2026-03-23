def test_sample_energy_curve_interpolates_hourly_points_from_unsorted_drag_path_and_clamps_levels():
    from pulse.ui.evening_input import CurvePoint, sample_energy_curve

    curve = [
        CurvePoint(minute_offset=480, level=12.5),
        CurvePoint(minute_offset=0, level=-3.0),
        CurvePoint(minute_offset=240, level="bad"),
        CurvePoint(minute_offset=900, level=10.0),
    ]

    samples = sample_energy_curve(curve, start_hour=8, end_hour=23)

    assert len(samples) == 16
    assert samples[0].hour == 8
    assert samples[0].level == 1.0
    assert samples[4].hour == 12
    assert samples[4].level == 1.0
    assert samples[8].hour == 16
    assert samples[8].level == 10.0
    assert samples[-1].hour == 23
    assert samples[-1].level == 10.0
    assert samples[6].hour == 14
    assert 1.0 <= samples[6].level <= 10.0


def test_sample_energy_curve_only_produces_levels_within_domain():
    from pulse.ui.evening_input import CurvePoint, sample_energy_curve

    curve = [
        CurvePoint(minute_offset=0, level=-100.0),
        CurvePoint(minute_offset=360, level=50.0),
        CurvePoint(minute_offset=900, level=3.0),
    ]

    samples = sample_energy_curve(curve, start_hour=8, end_hour=23)

    assert all(1.0 <= sample.level <= 10.0 for sample in samples)


def test_save_evening_input_persists_hourly_logs_and_context(tmp_path):
    from pulse.db import Database
    from pulse.ui.evening_input import HourlyEnergySample

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    samples = [
        HourlyEnergySample(hour=8, level=1.0),
        HourlyEnergySample(hour=9, level=2.0),
        HourlyEnergySample(hour=10, level=3.0),
    ]

    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=samples,
        sleep_hours=7.5,
        physical_activity="some",
        stress_level="low",
        free_note="heavy but manageable",
    )

    with db.connect() as connection:
        energy_rows = connection.execute(
            "SELECT date, hour, level FROM energy_logs ORDER BY hour"
        ).fetchall()
        context_row = connection.execute(
            "SELECT date, sleep_hours, physical_activity, stress_level, free_note FROM daily_context"
        ).fetchone()

    assert [(row["hour"], row["level"]) for row in energy_rows] == [(8, 1.0), (9, 2.0), (10, 3.0)]
    assert context_row["date"] == "2026-03-23"
    assert context_row["sleep_hours"] == 7.5
    assert context_row["physical_activity"] == "some"
    assert context_row["stress_level"] == "low"
    assert context_row["free_note"] == "heavy but manageable"


def test_save_evening_input_keeps_last_sample_for_duplicate_hours(tmp_path):
    from pulse.db import Database
    from pulse.ui.evening_input import HourlyEnergySample

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=[
            HourlyEnergySample(hour=8, level=1.0),
            HourlyEnergySample(hour=8, level=4.0),
            HourlyEnergySample(hour=9, level=2.0),
        ],
    )

    with db.connect() as connection:
        rows = connection.execute(
            "SELECT hour, level FROM energy_logs WHERE date = ? ORDER BY hour",
            ("2026-03-23",),
        ).fetchall()

    assert [(row["hour"], row["level"]) for row in rows] == [(8, 4.0), (9, 2.0)]


def test_save_evening_input_replaces_existing_day_submission(tmp_path):
    from pulse.db import Database
    from pulse.ui.evening_input import HourlyEnergySample

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=[HourlyEnergySample(hour=8, level=1.0)],
        free_note="first pass",
    )
    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=[HourlyEnergySample(hour=8, level=9.0), HourlyEnergySample(hour=9, level=8.0)],
        sleep_hours=8.0,
        physical_activity="yes",
        stress_level="high",
        free_note="second pass",
    )

    with db.connect() as connection:
        rows = connection.execute(
            "SELECT hour, level FROM energy_logs WHERE date = ? ORDER BY hour",
            ("2026-03-23",),
        ).fetchall()
        context_row = connection.execute(
            "SELECT sleep_hours, physical_activity, stress_level, free_note FROM daily_context WHERE date = ?",
            ("2026-03-23",),
        ).fetchone()

    assert [(row["hour"], row["level"]) for row in rows] == [(8, 9.0), (9, 8.0)]
    assert context_row["sleep_hours"] == 8.0
    assert context_row["physical_activity"] == "yes"
    assert context_row["stress_level"] == "high"
    assert context_row["free_note"] == "second pass"


def test_save_evening_input_clamps_invalid_hour_and_level_at_persistence_boundary(tmp_path):
    from pulse.db import Database

    class RawSample(object):
        def __init__(self, hour, level):
            self.hour = hour
            self.level = level

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_evening_input(
        date="2026-03-23",
        hourly_samples=[
            RawSample(hour=-5, level=-100),
            RawSample(hour=6, level=4),
            RawSample(hour=99, level=50),
        ],
    )

    with db.connect() as connection:
        rows = connection.execute(
            "SELECT hour, level FROM energy_logs WHERE date = ? ORDER BY hour",
            ("2026-03-23",),
        ).fetchall()

    assert [(row["hour"], row["level"]) for row in rows] == [(8, 4.0), (23, 10.0)]
