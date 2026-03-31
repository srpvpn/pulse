def test_evening_page_model_describes_sections_and_primary_action():
    from pulse.ui.evening_input import build_curve_editor_layout, build_evening_page_model

    view_model = build_evening_page_model()
    curve_layout = build_curve_editor_layout()

    assert view_model.title == "Evening Check-In"
    assert view_model.primary_action == "Save today"
    assert view_model.section_titles == (
        "Energy curve",
        "Recovery inputs",
        "Context note",
    )
    assert view_model.has_summary_card is False
    assert view_model.choice_style == "compact"
    assert view_model.sticky_primary_action is False
    assert view_model.fills_viewport is True
    assert view_model.large_primary_action is True
    assert view_model.keyboard_editor_hidden_by_default is True
    assert view_model.sleep_scale_draws_value is False
    assert view_model.sleep_scale_focusable is False
    assert view_model.max_content_width == 960
    assert view_model.responsive_layout is True
    assert view_model.scroll_policy == "automatic"
    assert curve_layout.minimum_width == 280
    assert curve_layout.height == 280
