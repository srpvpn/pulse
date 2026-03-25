def test_main_window_defaults_to_sidebar_shell_after_onboarding():
    from pulse.main import AppShellState
    from pulse.ui.main_window import PulseMainWindow

    window = PulseMainWindow(application=None, initial_state=AppShellState("dashboard", "20:00"))

    assert window.current_view == "dashboard"
    assert window.nav_items == (
        ("dashboard", "nav.dashboard"),
        ("evening", "nav.evening"),
        ("patterns", "nav.patterns"),
        ("review", "nav.review"),
        ("rituals", "nav.rituals"),
        ("settings", "nav.settings"),
    )
    assert window.uses_fixed_sidebar_width is True
    assert window.supports_narrow_layout is True
    assert window.uses_overlay_split_view is True
    assert window.uses_window_breakpoints is True
    assert window.uses_header_bar_top_chrome is True


def test_layout_mode_switches_for_narrow_widths():
    from pulse.ui.main_window import _layout_mode_for_width

    assert _layout_mode_for_width(640) == "narrow"
    assert _layout_mode_for_width(1000) == "narrow"
    assert _layout_mode_for_width(1200) == "wide"
