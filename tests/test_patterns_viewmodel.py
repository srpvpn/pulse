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
        ),
        PatternCorrelation(
            label="Decision load vs evening energy",
            delta=-1.7,
            condition="after 12+ switches",
            science_ref="Ego Depletion (Baumeister, 1998)",
        ),
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
        selected_range="30D",
    )

    assert view_model.heatmap_caption == "Heatmap covers 4 daily blocks"
    assert view_model.correlation_cards[0].summary == (
        "Sleep vs next-day energy: 2.3 points higher after 7+ hours of sleep"
    )
    assert view_model.correlation_cards[1].summary == (
        "Decision load vs evening energy: 1.7 points lower after 12+ switches"
    )
    assert view_model.trajectory_summary == "Burnout score has fallen for 2 days"
    assert view_model.selected_range == "30D"


def test_build_patterns_view_model_builds_daily_rhythm_blocks_for_short_ranges():
    from pulse.pattern_engine import DailyEnergyPoint
    from pulse.ui.patterns import build_patterns_view_model

    daily_points = [
        DailyEnergyPoint(date="2026-03-16", average_energy=8.0),
        DailyEnergyPoint(date="2026-03-18", average_energy=4.0),
        DailyEnergyPoint(date="2026-03-22", average_energy=6.0),
    ]

    view_model = build_patterns_view_model(
        daily_points=daily_points,
        correlations=[],
        trajectory_scores=[],
        selected_range="30D",
    )

    assert view_model.heatmap_layout == "rhythm"
    assert [block.label for block in view_model.rhythm_blocks] == ["Mar 16", "Mar 18", "Mar 22"]
    assert [block.energy for block in view_model.rhythm_blocks] == [8.0, 4.0, 6.0]
    assert [block.color for block in view_model.rhythm_blocks] == ["#1D9E75", "#EF9F27", "#93B75D"]
    assert len(view_model.rhythm_summary) == 3
    assert view_model.rhythm_summary[0] == "Average energy 6.0 across this range"


def test_build_patterns_view_model_builds_weekly_or_monthly_rhythm_blocks_for_long_ranges():
    from pulse.pattern_engine import DailyEnergyPoint
    from pulse.ui.patterns import build_patterns_view_model

    daily_points = [
        DailyEnergyPoint(date="2026-01-10", average_energy=8.0),
        DailyEnergyPoint(date="2026-01-20", average_energy=6.0),
        DailyEnergyPoint(date="2026-02-10", average_energy=4.0),
    ]

    view_model = build_patterns_view_model(
        daily_points=daily_points,
        correlations=[],
        trajectory_scores=[],
        selected_range="1Y",
    )

    assert view_model.heatmap_layout == "rhythm"
    assert [block.label for block in view_model.rhythm_blocks] == ["Jan", "Feb"]
    assert [block.energy for block in view_model.rhythm_blocks] == [7.0, 4.0]
    assert view_model.rhythm_blocks[0].color == "#93B75D"
    assert view_model.rhythm_blocks[1].color == "#EF9F27"


def test_build_patterns_view_model_reports_rising_trajectory_for_latest_streak():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.patterns import build_patterns_view_model

    trajectory_scores = [
        BurnoutScoreResult(score=55.0, ali=0.0, rqs=0.0, trend_penalty=0.0, mbi_correction=0.0),
        BurnoutScoreResult(score=58.0, ali=0.0, rqs=0.0, trend_penalty=0.0, mbi_correction=0.0),
        BurnoutScoreResult(score=63.0, ali=0.0, rqs=0.0, trend_penalty=0.0, mbi_correction=0.0),
    ]

    view_model = build_patterns_view_model(
        daily_points=[],
        correlations=[],
        trajectory_scores=trajectory_scores,
        selected_range="7D",
    )

    assert view_model.trajectory_summary == "Burnout score has risen for 2 days"


def test_build_patterns_view_model_localizes_russian_strings():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.pattern_engine import DailyEnergyPoint
    from pulse.ui.patterns import PatternCorrelation, build_patterns_view_model

    view_model = build_patterns_view_model(
        daily_points=[DailyEnergyPoint(date="2026-03-16", average_energy=8.0)],
        correlations=[
            PatternCorrelation(
                label="Sleep vs next-day energy",
                delta=2.3,
                condition="after 7+ hours of sleep",
                science_ref="Sleep and cognitive performance (Walker, 2017)",
            )
        ],
        trajectory_scores=[
            BurnoutScoreResult(score=55.0, ali=0.0, rqs=0.0, trend_penalty=0.0, mbi_correction=0.0),
            BurnoutScoreResult(score=58.0, ali=0.0, rqs=0.0, trend_penalty=0.0, mbi_correction=0.0),
        ],
        selected_range="30D",
        language="ru",
    )

    assert view_model.heatmap_caption == "Тепловая карта за 1 дневной блок"
    assert view_model.correlation_cards[0].summary == (
        "Сон и энергия следующего дня: на 2.3 пункта выше после 7+ часов сна"
    )
    assert view_model.trajectory_summary == "Балл выгорания рос 1 день"
    assert view_model.rhythm_blocks[0].label == "16 мар"
    assert view_model.rhythm_summary[0] == "Средняя энергия 8.0 за этот период"
