def test_build_patterns_view_model_formats_correlations_and_trajectory_summary():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.pattern_engine import DailyEnergyPoint
    from pulse.ui.patterns import PatternCorrelation, build_patterns_view_model

    daily_points = [
        DailyEnergyPoint(date="2026-03-18", average_energy=8.0),
        DailyEnergyPoint(date="2026-03-19", average_energy=7.0),
        DailyEnergyPoint(date="2026-03-20", average_energy=6.0),
        DailyEnergyPoint(date="2026-03-21", average_energy=5.0),
    ]
    correlations = [
        PatternCorrelation(
            label="Sleep vs next-day energy",
            delta=2.3,
            condition="after 7+ hours of sleep",
            science_ref="Sleep and cognitive performance (Walker, 2017)",
        )
    ]
    trajectory_scores = [
        BurnoutScoreResult(score=62.0, ali=4.0, rqs=70.0, trend_penalty=0.0, mbi_correction=0.0),
        BurnoutScoreResult(score=58.0, ali=4.2, rqs=69.0, trend_penalty=0.0, mbi_correction=0.0),
        BurnoutScoreResult(score=55.0, ali=4.5, rqs=68.0, trend_penalty=0.0, mbi_correction=0.0),
    ]

    view_model = build_patterns_view_model(
        daily_points=daily_points,
        correlations=correlations,
        trajectory_scores=trajectory_scores,
    )

    assert view_model.heatmap_caption == "Heatmap covers 4 days"
    assert view_model.correlation_cards[0].summary == (
        "Sleep vs next-day energy: 2.3 points higher after 7+ hours of sleep"
    )
    assert view_model.correlation_cards[0].science_ref == "Sleep and cognitive performance (Walker, 2017)"
    assert view_model.trajectory_summary == "Burnout score has fallen for 3 days"


def test_build_patterns_view_model_builds_heatmap_cells_from_sorted_days():
    from pulse.pattern_engine import DailyEnergyPoint
    from pulse.ui.patterns import build_patterns_view_model

    daily_points = [
        DailyEnergyPoint(date="2026-03-20", average_energy=4.0),
        DailyEnergyPoint(date="2026-03-18", average_energy=8.0),
    ]

    view_model = build_patterns_view_model(
        daily_points=daily_points,
        correlations=[],
        trajectory_scores=[],
    )

    assert [cell.date for cell in view_model.heatmap_cells] == ["2026-03-18", "2026-03-20"]
    assert view_model.heatmap_cells[0].color == "#1D9E75"
    assert view_model.heatmap_cells[1].color == "#EF9F27"
