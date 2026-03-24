def test_seed_demo_data_creates_entries_for_all_primary_screens(tmp_path):
    from pulse.db import Database
    from pulse.dev_seed import seed_demo_data

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    seed_demo_data(db)

    with db.connect() as connection:
        energy_count = connection.execute("SELECT COUNT(*) AS count FROM energy_logs").fetchone()["count"]
        context_count = connection.execute("SELECT COUNT(*) AS count FROM daily_context").fetchone()["count"]
        ritual_count = connection.execute("SELECT COUNT(*) AS count FROM rituals").fetchone()["count"]
        mbi_count = connection.execute("SELECT COUNT(*) AS count FROM mbi_checkins").fetchone()["count"]

    assert energy_count > 0
    assert context_count > 0
    assert ritual_count > 0
    assert mbi_count > 0
