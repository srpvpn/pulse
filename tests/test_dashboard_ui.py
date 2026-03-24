def test_dashboard_view_model_exposes_hero_and_secondary_metrics():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.dashboard import build_dashboard_view_model

    score = BurnoutScoreResult(
        score=72.0,
        ali=3.8,
        rqs=81.0,
        trend_penalty=5.0,
        mbi_correction=2.0,
    )

    view_model = build_dashboard_view_model(score, None, ultradian_cycles=3)

    assert view_model.score_label == "72"
    assert view_model.zone_pill == "Healthy zone"
    assert [item.label for item in view_model.secondary_metrics] == [
        "Recovery quality",
        "Accumulated fatigue",
        "Ultradian cycles",
    ]
    assert view_model.secondary_metrics[0].value == "81"


def test_dashboard_view_model_matches_reference_composition():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.dashboard import build_dashboard_view_model

    score = BurnoutScoreResult(
        score=82.0,
        ali=2.9,
        rqs=86.0,
        trend_penalty=2.0,
        mbi_correction=1.0,
    )

    view_model = build_dashboard_view_model(score, None, ultradian_cycles=2)

    assert view_model.headline == "Good morning."
    assert view_model.score_card_title == "Current Burnout Score"
    assert view_model.insight_title == "Daily Insight"
    assert [item.label for item in view_model.reference_cards] == [
        "Recovery direction",
        "Ultradian cycles",
    ]
    assert view_model.reference_cards[0].items == ["Load is stable"]
    assert view_model.reference_cards[1].items == ["2 completed today"]
