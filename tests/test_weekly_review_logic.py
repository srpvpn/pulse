def test_build_weekly_review_view_model_formats_summary_and_rotates_science_card():
    from pulse.ui.weekly_review import MBICheckin, build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        this_week_average_energy=6.8,
        previous_week_average_energy=5.5,
        mbi_checkin=MBICheckin(exhaustion=3, cynicism=2, efficacy=1),
        week_index=1,
    )

    assert view_model.energy_summary == "Average energy 6.8 this week vs 5.5 last week (+1.3)"
    assert view_model.mbi_correction == -2.0
    assert view_model.science_card.title == "Psychological detachment"
    assert "switching off" in view_model.science_card.body.lower()


def test_build_weekly_review_view_model_returns_first_science_card_for_week_zero():
    from pulse.ui.weekly_review import build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        this_week_average_energy=5.0,
        previous_week_average_energy=5.0,
        mbi_checkin=None,
        week_index=0,
    )

    assert view_model.science_card.title == "Ultradian rhythms"
    assert view_model.energy_summary == "Average energy 5.0 this week vs 5.0 last week (+0.0)"
    assert view_model.mbi_correction == 0.0
