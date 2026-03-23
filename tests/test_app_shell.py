def test_first_launch_routes_to_onboarding(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    state = app.build_state()

    assert state.current_view == "onboarding"
    assert state.reminder_time == "20:00"


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


def test_main_window_uses_initial_state_for_routing():
    from pulse.main import AppShellState
    from pulse.ui.main_window import PulseMainWindow

    state = AppShellState(current_view="evening", reminder_time="21:30")

    window = PulseMainWindow(application=None, initial_state=state)

    assert window.current_view == "evening"
