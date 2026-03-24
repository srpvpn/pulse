def test_weekly_review_view_model_defaults_to_plain_cards():
    from pulse.ui.weekly_review import build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        week_start="2026-03-23",
        week_end="2026-03-29",
        this_week_average_energy=5.0,
        previous_week_average_energy=4.5,
        insights=[],
        week_index=0,
    )

    assert view_model.card_style == "plain"
