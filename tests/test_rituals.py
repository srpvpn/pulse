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
    original_send = PulseApplication._send_ritual_notification

    try:
        PulseApplication._send_ritual_notification = lambda self, ritual, language: True
        due = app.notify_due_rituals(current_date="2026-03-23", current_time="20:15")
        repeat = app.notify_due_rituals(current_date="2026-03-23", current_time="20:20")
    finally:
        PulseApplication._send_ritual_notification = original_send

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


def test_activate_starts_notification_scheduler_and_checks_due_rituals_once(tmp_path, monkeypatch):
    from pulse.main import PulseApplication
    import pulse.main as main_module

    scheduled = []
    notified = []
    presented = []

    class FakeGLib:
        @staticmethod
        def timeout_add_seconds(interval, callback):
            scheduled.append((interval, callback))
            return 17

    class FakeWindow:
        def __init__(self, application=None, initial_state=None):
            self.application = application
            self.initial_state = initial_state

        def present(self):
            presented.append(True)

    monkeypatch.setattr(main_module, "GLib", FakeGLib)
    monkeypatch.setattr(main_module, "PulseMainWindow", FakeWindow)
    monkeypatch.setattr(PulseApplication, "_current_time_text", lambda self: "20:15")
    monkeypatch.setattr(
        PulseApplication,
        "notify_due_rituals",
        lambda self, current_time, current_date=None: notified.append((current_time, current_date)) or [],
    )

    app = PulseApplication(data_dir=tmp_path)

    app.do_activate()
    app.do_activate()

    assert presented == [True, True]
    assert notified == [("20:15", None)]
    assert len(scheduled) == 1
    assert scheduled[0][0] == 60
    assert app._notification_source_id == 17


def test_notify_due_rituals_falls_back_to_notify_send_when_gio_unavailable(tmp_path, monkeypatch):
    from pulse.main import PulseApplication
    import pulse.main as main_module

    sent = []

    def fake_run(command, check):
        sent.append((command, check))
        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(main_module, "Gio", None)
    monkeypatch.setattr(main_module.shutil, "which", lambda name: "/usr/bin/notify-send" if name == "notify-send" else None)
    monkeypatch.setattr(main_module.subprocess, "run", fake_run)

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_ritual(ritual_id="walk", label="Walk outside", time="15:48", active=True)

    due = app.notify_due_rituals(current_date="2026-03-24", current_time="15:49")

    assert [item.ritual_id for item in due] == ["walk"]
    assert sent == [
        (
            [
                "/usr/bin/notify-send",
                "-a",
                "Pulse",
                "-i",
                "com.example.Pulse",
                "Walk outside",
                "Scheduled for 15:48",
            ],
            False,
        )
    ]


def test_notify_due_rituals_prefers_notify_send_over_gio_when_available(tmp_path, monkeypatch):
    from pulse.main import PulseApplication
    import pulse.main as main_module

    sent = []
    gio_calls = []

    def fake_run(command, check):
        sent.append((command, check))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(main_module.shutil, "which", lambda name: "/usr/bin/notify-send" if name == "notify-send" else None)
    monkeypatch.setattr(main_module.subprocess, "run", fake_run)
    original_gio = PulseApplication._notify_with_gio

    try:
        PulseApplication._notify_with_gio = lambda self, ritual, language: gio_calls.append(ritual.ritual_id) or True
        app = PulseApplication(data_dir=tmp_path)
        app.database.save_ritual(ritual_id="walk", label="Walk outside", time="15:48", active=True)

        due = app.notify_due_rituals(current_date="2026-03-24", current_time="15:49")
    finally:
        PulseApplication._notify_with_gio = original_gio

    assert [item.ritual_id for item in due] == ["walk"]
    assert len(sent) == 1
    assert gio_calls == []


def test_notify_due_rituals_does_not_mark_delivery_when_transport_fails(tmp_path, monkeypatch):
    from pulse.main import PulseApplication
    import pulse.main as main_module

    monkeypatch.setattr(main_module, "Gio", None)
    monkeypatch.setattr(main_module.shutil, "which", lambda name: "/usr/bin/notify-send" if name == "notify-send" else None)

    def fake_run(command, check):
        class Result:
            returncode = 1

        return Result()

    monkeypatch.setattr(main_module.subprocess, "run", fake_run)

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_ritual(ritual_id="walk", label="Walk outside", time="15:48", active=True)

    first = app.notify_due_rituals(current_date="2026-03-24", current_time="15:49")
    second = app.notify_due_rituals(current_date="2026-03-24", current_time="15:50")

    assert [item.ritual_id for item in first] == ["walk"]
    assert [item.ritual_id for item in second] == ["walk"]
    assert app.database.list_delivered_ritual_ids("2026-03-24") == []
