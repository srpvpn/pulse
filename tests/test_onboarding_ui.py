def test_onboarding_content_model_matches_premium_landing_copy():
    from pulse.ui.onboarding import ONBOARDING_CTA_LABEL, ONBOARDING_STEPS

    assert ONBOARDING_CTA_LABEL == "Start tracking tonight"
    assert len(ONBOARDING_STEPS) == 3
    assert ONBOARDING_STEPS[0][0] == "Draw the day"


def test_onboarding_page_model_uses_compact_reference_layout():
    from pulse.ui.onboarding import build_onboarding_page_model

    view_model = build_onboarding_page_model("20:00")

    assert view_model.headline == "Track energy nightly."
    assert view_model.badge == "Local-first burnout tracking"
    assert view_model.reminder_title == "Evening reminder"
    assert view_model.feature_columns == 3
