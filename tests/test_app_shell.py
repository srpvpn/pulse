def test_first_launch_routes_to_onboarding(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    state = app.build_state()

    assert state.current_view == "onboarding"
    assert state.reminder_time == "20:00"
    assert state.language == "en"
    assert state.theme_mode == "system"


def test_completing_onboarding_routes_to_evening(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    state = app.complete_onboarding("21:30")

    assert state.current_view == "evening"
    assert state.reminder_time == "21:30"
    assert app.build_state().current_view == "evening"


def test_reloading_persisted_onboarding_state_returns_evening(tmp_path):
    from pulse.main import PulseApplication

    first_app = PulseApplication(data_dir=tmp_path)
    first_app.complete_onboarding("21:30")

    second_app = PulseApplication(data_dir=tmp_path)
    state = second_app.build_state()

    assert state.current_view == "evening"
    assert state.reminder_time == "21:30"


def test_malformed_settings_falls_back_to_default_state(tmp_path):
    from pulse.main import PulseApplication

    settings_path = tmp_path / "pulse-settings.json"
    settings_path.write_text("{not valid json", encoding="utf-8")

    app = PulseApplication(data_dir=tmp_path)
    state = app.build_state()

    assert state.current_view == "onboarding"
    assert state.reminder_time == "20:00"


def test_non_boolean_onboarding_complete_falls_back_to_onboarding(tmp_path):
    from json import dumps

    from pulse.main import PulseApplication

    settings_path = tmp_path / "pulse-settings.json"
    settings_path.write_text(
        dumps({"onboarding_complete": "yes", "reminder_time": "21:30"}),
        encoding="utf-8",
    )

    app = PulseApplication(data_dir=tmp_path)
    state = app.build_state()

    assert state.current_view == "onboarding"
    assert state.reminder_time == "21:30"


def test_application_persists_language_selection(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    state = app.set_language("ru")

    assert state.language == "ru"
    assert app.build_state().language == "ru"


def test_application_persists_theme_mode_selection(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    state = app.set_theme_mode("dark")

    assert state.theme_mode == "dark"
    assert app.build_state().theme_mode == "dark"


def test_invalid_theme_mode_falls_back_to_system(tmp_path):
    from json import dumps

    from pulse.main import PulseApplication

    settings_path = tmp_path / "pulse-settings.json"
    settings_path.write_text(
        dumps(
            {
                "onboarding_complete": True,
                "reminder_time": "21:30",
                "language": "ru",
                "theme_mode": "sepia",
            }
        ),
        encoding="utf-8",
    )

    app = PulseApplication(data_dir=tmp_path)
    state = app.build_state()

    assert state.current_view == "evening"
    assert state.reminder_time == "21:30"
    assert state.language == "ru"
    assert state.theme_mode == "system"


def test_main_window_uses_initial_state_for_routing():
    from pulse.main import AppShellState
    from pulse.ui.main_window import PulseMainWindow

    state = AppShellState(current_view="evening", reminder_time="21:30")

    window = PulseMainWindow(application=None, initial_state=state)

    assert window.current_view == "evening"


def test_main_window_keeps_application_reference():
    from pulse.main import AppShellState
    from pulse.ui.main_window import PulseMainWindow

    application = object()
    window = PulseMainWindow(application=application, initial_state=AppShellState("onboarding", "20:00"))

    assert window.application is application
    assert window.uses_compact_stack_sizing is True


def test_main_window_dashboard_path_handles_saved_weekly_checkin_without_crashing(tmp_path):
    from pulse.main import AppShellState, PulseApplication
    from pulse.ui.evening_input import HourlyEnergySample
    from pulse.ui.main_window import PulseMainWindow

    app = PulseApplication(data_dir=tmp_path)
    app.complete_onboarding("20:00")
    app.database.save_evening_input(
        date="2026-03-23",
        hourly_samples=[HourlyEnergySample(hour=8, level=5.0), HourlyEnergySample(hour=9, level=6.0)],
        sleep_hours=7.0,
        stress_level="low",
    )
    app.database.save_weekly_checkin(
        week="2026-03-23",
        exhaustion=2,
        cynicism=1,
        efficacy=3,
        note="Keep Friday lighter",
    )

    window = PulseMainWindow(
        application=app,
        initial_state=AppShellState(current_view="dashboard", reminder_time="20:00"),
    )

    assert window.current_view == "dashboard"


def test_latest_mbi_correction_uses_saved_checkin_directly(tmp_path):
    from pulse.main import AppShellState, PulseApplication
    from pulse.ui.main_window import PulseMainWindow

    app = PulseApplication(data_dir=tmp_path)
    app.database.save_weekly_checkin(
        week="2026-03-23",
        exhaustion=4,
        cynicism=4,
        efficacy=0,
        note="Hard week",
    )

    window = PulseMainWindow(
        application=app,
        initial_state=AppShellState(current_view="dashboard", reminder_time="20:00"),
    )

    assert window._latest_mbi_correction() == -10.0


def test_dashboard_empty_state_keeps_reference_cards_for_first_run(tmp_path, monkeypatch):
    from pulse.main import AppShellState, PulseApplication
    import pulse.ui.main_window as main_window_module
    from pulse.ui.main_window import PulseMainWindow

    captured = {}
    original_create_dashboard_page = main_window_module.create_dashboard_page

    def fake_create_dashboard_page(view_model, has_data=True):
        captured["view_model"] = view_model
        captured["has_data"] = has_data
        return view_model

    monkeypatch.setattr(main_window_module, "create_dashboard_page", fake_create_dashboard_page)

    try:
        app = PulseApplication(data_dir=tmp_path)
        window = PulseMainWindow(
            application=app,
            initial_state=AppShellState(current_view="dashboard", reminder_time="20:00"),
        )
        window._build_dashboard_page()
    finally:
        monkeypatch.setattr(main_window_module, "create_dashboard_page", original_create_dashboard_page)

    assert captured["has_data"] is False
    assert len(captured["view_model"].reference_cards) == 2
