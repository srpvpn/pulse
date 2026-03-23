def test_due_rituals_returns_active_rituals_due_at_or_before_now():
    from pulse.ui.rituals import Ritual, due_rituals_for_time

    rituals = [
        Ritual(ritual_id="evening-input", label="Evening input", time="20:00", active=True),
        Ritual(ritual_id="weekly-review", label="Weekly review", time="19:00", active=True),
        Ritual(ritual_id="disabled", label="Disabled", time="18:00", active=False),
    ]

    due = due_rituals_for_time(rituals, current_time="19:30")

    assert [ritual.ritual_id for ritual in due] == ["weekly-review"]


def test_database_persists_and_updates_rituals(tmp_path):
    from pulse.db import Database

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    db.save_ritual(ritual_id="evening-input", label="Evening input", time="20:00", active=True)
    db.save_ritual(ritual_id="evening-input", label="Evening input", time="21:00", active=False)

    rituals = db.list_rituals()

    assert len(rituals) == 1
    assert rituals[0]["ritual_id"] == "evening-input"
    assert rituals[0]["time"] == "21:00"
    assert rituals[0]["active"] == 0


def test_application_plans_due_ritual_notifications_without_gio(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_ritual(ritual_id="evening-input", label="Evening input", time="20:00", active=True)
    app.database.save_ritual(ritual_id="weekly-review", label="Weekly review", time="19:00", active=True)

    plan = app.plan_notifications(current_date="2026-03-23", current_time="20:30")

    assert [item.ritual_id for item in plan] == ["weekly-review", "evening-input"]


def test_notify_due_rituals_records_delivery_and_suppresses_repeat_calls(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_ritual(ritual_id="evening-input", label="Evening input", time="20:00", active=True)

    due = app.notify_due_rituals(current_date="2026-03-23", current_time="20:15")
    repeat = app.notify_due_rituals(current_date="2026-03-23", current_time="20:20")

    assert [item.ritual_id for item in due] == ["evening-input"]
    assert repeat == []


def test_startup_after_due_only_plans_undelivered_rituals(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_ritual(ritual_id="evening-input", label="Evening input", time="20:00", active=True)
    app.database.save_ritual(ritual_id="weekly-review", label="Weekly review", time="19:00", active=True)

    app.database.mark_ritual_delivered(
        current_date="2026-03-23",
        ritual_id="weekly-review",
        delivered_time="19:05",
    )

    plan = app.plan_notifications(current_date="2026-03-23", current_time="20:30")

    assert [item.ritual_id for item in plan] == ["evening-input"]
