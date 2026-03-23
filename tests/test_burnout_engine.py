def _entry(day, energy, sleep_hours=7.5, stress_level="low"):
    from pulse.burnout_engine import BurnoutEntry

    return BurnoutEntry(
        date="2026-03-%02d" % day,
        average_energy=energy,
        sleep_hours=sleep_hours,
        stress_level=stress_level,
    )


def test_compute_allostatic_load_index_gives_equal_weight_within_oldest_band():
    from pulse.burnout_engine import compute_allostatic_load_index

    base_entries = [_entry(day, 10.0) for day in range(1, 15)]

    day_two_drop = list(base_entries)
    day_two_drop[1] = _entry(2, 0.0)

    day_four_drop = list(base_entries)
    day_four_drop[3] = _entry(4, 0.0)

    assert compute_allostatic_load_index(day_two_drop) == compute_allostatic_load_index(day_four_drop)


def test_compute_allostatic_load_index_weights_recent_days_three_times_more_than_oldest_band():
    from pytest import approx
    from pulse.burnout_engine import compute_allostatic_load_index

    base_entries = [_entry(day, 10.0) for day in range(1, 15)]

    oldest_drop = list(base_entries)
    oldest_drop[1] = _entry(2, 0.0)

    newest_drop = list(base_entries)
    newest_drop[13] = _entry(14, 0.0)

    ratio = compute_allostatic_load_index(newest_drop) / compute_allostatic_load_index(oldest_drop)

    assert ratio == approx(3.0)


def test_compute_burnout_score_without_mbi_uses_available_inputs():
    from pulse.burnout_engine import compute_burnout_score

    result = compute_burnout_score([_entry(day, 8.0) for day in range(1, 15)])

    assert result.score == 99.0
    assert result.ali == 2.0
    assert result.rqs == 100.0
    assert result.trend_penalty == 0.0
    assert result.mbi_correction == 0.0


def test_compute_trend_penalty_uses_decline_streak_ending_today():
    from pulse.burnout_engine import compute_trend_penalty

    entries = [
        _entry(1, 10.0),
        _entry(2, 9.0),
        _entry(3, 8.0),
        _entry(4, 7.0),
        _entry(5, 6.0),
        _entry(6, 9.0),
        _entry(7, 10.0),
        _entry(8, 9.0),
        _entry(9, 8.0),
        _entry(10, 9.0),
        _entry(11, 10.0),
        _entry(12, 9.0),
        _entry(13, 8.0),
        _entry(14, 7.0),
    ]

    assert compute_trend_penalty(entries) == 60.0


def test_compute_burnout_score_clips_and_uses_fallback_context_on_decline():
    from pulse.burnout_engine import compute_burnout_score

    entries = [
        _entry(day, 11.0 - day, sleep_hours=8.0 if day <= 7 else None, stress_level="low" if day <= 7 else None)
        for day in range(1, 15)
    ]

    result = compute_burnout_score(entries)

    assert result.ali == 7.5
    assert result.rqs == 100.0
    assert result.trend_penalty == 660.0
    assert result.score == 0.0
