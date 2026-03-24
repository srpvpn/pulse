def test_generate_weekly_insights_prioritizes_end_of_week_drop_and_sleep_warning():
    from pulse.pattern_engine import WeeklyInsightDay, generate_weekly_insights

    week_data = [
        WeeklyInsightDay(date="2026-03-23", avg_energy=8.0, sleep_hours=6.0, physical_activity="some"),
        WeeklyInsightDay(date="2026-03-24", avg_energy=7.6, sleep_hours=6.2, physical_activity="yes"),
        WeeklyInsightDay(date="2026-03-25", avg_energy=7.1, sleep_hours=6.1, physical_activity="some"),
        WeeklyInsightDay(date="2026-03-26", avg_energy=6.0, sleep_hours=6.0, physical_activity="none"),
        WeeklyInsightDay(date="2026-03-27", avg_energy=5.1, sleep_hours=5.9, physical_activity="none"),
    ]

    insights = generate_weekly_insights(week_data)

    assert len(insights) >= 2
    assert insights[0].type == "warning"
    assert "last 3 days" in insights[0].body.lower()
    assert any("average sleep" in insight.body.lower() for insight in insights)


def test_generate_weekly_insights_includes_best_vs_worst_day_and_activity_signal():
    from pulse.pattern_engine import WeeklyInsightDay, generate_weekly_insights

    week_data = [
        WeeklyInsightDay(date="2026-03-23", avg_energy=4.0, sleep_hours=7.0, physical_activity="none"),
        WeeklyInsightDay(date="2026-03-24", avg_energy=5.0, sleep_hours=7.0, physical_activity="yes"),
        WeeklyInsightDay(date="2026-03-25", avg_energy=6.0, sleep_hours=7.5, physical_activity="some"),
        WeeklyInsightDay(date="2026-03-26", avg_energy=7.0, sleep_hours=7.2, physical_activity="yes"),
        WeeklyInsightDay(date="2026-03-27", avg_energy=8.5, sleep_hours=7.6, physical_activity="some"),
    ]

    insights = generate_weekly_insights(week_data)

    assert len(insights) >= 2
    assert any(
        "best day" in insight.title.lower() or "best day" in insight.body.lower()
        for insight in insights
    )
    assert any("physical activity" in insight.body.lower() for insight in insights)


def test_generate_weekly_insights_localizes_russian_output():
    from pulse.pattern_engine import WeeklyInsightDay, generate_weekly_insights

    week_data = [
        WeeklyInsightDay(date="2026-03-23", avg_energy=8.0, sleep_hours=6.0, physical_activity="some"),
        WeeklyInsightDay(date="2026-03-24", avg_energy=7.6, sleep_hours=6.2, physical_activity="yes"),
        WeeklyInsightDay(date="2026-03-25", avg_energy=7.1, sleep_hours=6.1, physical_activity="some"),
        WeeklyInsightDay(date="2026-03-26", avg_energy=6.0, sleep_hours=6.0, physical_activity="none"),
        WeeklyInsightDay(date="2026-03-27", avg_energy=5.1, sleep_hours=5.9, physical_activity="none"),
    ]

    insights = generate_weekly_insights(week_data, language="ru")

    assert insights[0].type == "warning"
    assert "последние 3 дня" in insights[0].body.lower()
    assert any("средний сон" in insight.body.lower() for insight in insights)
