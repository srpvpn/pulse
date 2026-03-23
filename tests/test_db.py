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
