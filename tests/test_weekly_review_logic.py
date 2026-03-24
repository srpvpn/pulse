def test_build_weekly_review_view_model_formats_heading_and_rotates_science_card():
    from pulse.pattern_engine import WeeklyInsight
    from pulse.ui.weekly_review import build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        week_start="2026-03-23",
        week_end="2026-03-29",
        this_week_average_energy=6.8,
        previous_week_average_energy=5.5,
        insights=[
            WeeklyInsight(
                title="Best vs worst day",
                body="Best day was Wednesday, worst day was Friday. Gap 2.1 points.",
                type="neutral",
            )
        ],
        week_index=1,
    )

    assert view_model.week_title == "Week Mar 23 - Mar 29"
    assert view_model.energy_summary == "Average energy 6.8 - 1.3 higher than last week"
    assert view_model.science_card.title == "Psychological detachment"
    assert view_model.insights[0].title == "Best vs worst day"


def test_build_weekly_review_view_model_handles_flat_delta_and_empty_insights():
    from pulse.ui.weekly_review import build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        week_start="2026-03-23",
        week_end="2026-03-29",
        this_week_average_energy=5.0,
        previous_week_average_energy=5.0,
        insights=[],
        week_index=0,
    )

    assert view_model.science_card.title == "Ultradian rhythms"
    assert view_model.energy_summary == "Average energy 5.0 - unchanged from last week"
    assert view_model.insights == []


def test_compute_mbi_correction_clips_to_intended_range():
    from pulse.ui.weekly_review import MBICheckin, compute_mbi_correction

    assert compute_mbi_correction(MBICheckin(exhaustion=4, cynicism=4, efficacy=0)) == -10.0
    assert compute_mbi_correction(MBICheckin(exhaustion=0, cynicism=0, efficacy=4)) == 10.0
    assert compute_mbi_correction(MBICheckin(exhaustion=9, cynicism=9, efficacy=-2)) == -10.0
    assert compute_mbi_correction(MBICheckin(exhaustion=-3, cynicism=-3, efficacy=9)) == 10.0


def test_build_weekly_review_view_model_localizes_russian_copy():
    from pulse.pattern_engine import WeeklyInsight
    from pulse.ui.weekly_review import build_weekly_review_view_model

    view_model = build_weekly_review_view_model(
        week_start="2026-03-23",
        week_end="2026-03-29",
        this_week_average_energy=6.8,
        previous_week_average_energy=5.5,
        insights=[
            WeeklyInsight(
                title="Лучший и худший день",
                body="Лучший день был в среду, худший — в пятницу.",
                type="neutral",
            )
        ],
        week_index=1,
        language="ru",
    )

    assert view_model.week_title == "Неделя 23 мар - 29 мар"
    assert view_model.energy_summary == "Средняя энергия 6.8 - на 1.3 выше прошлой недели"
    assert view_model.science_card.title == "Психологическое отключение"
