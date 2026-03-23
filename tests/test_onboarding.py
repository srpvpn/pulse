def test_normalize_reminder_time_defaults_outside_evening_window():
    from pulse.ui.onboarding import normalize_reminder_time

    assert normalize_reminder_time("17:30") == "20:00"
    assert normalize_reminder_time("22:30") == "20:00"


def test_normalize_reminder_time_accepts_evening_window_bounds():
    from pulse.ui.onboarding import normalize_reminder_time

    assert normalize_reminder_time("18:00") == "18:00"
    assert normalize_reminder_time("22:00") == "22:00"
