def test_count_consecutive_low_energy_days_counts_latest_low_streak():
    from pulse.pattern_engine import DailyEnergyPoint, count_consecutive_low_energy_days

    points = [
        DailyEnergyPoint(date="2026-03-18", average_energy=7.5),
        DailyEnergyPoint(date="2026-03-19", average_energy=4.5),
        DailyEnergyPoint(date="2026-03-20", average_energy=4.0),
        DailyEnergyPoint(date="2026-03-21", average_energy=3.5),
    ]

    assert count_consecutive_low_energy_days(points, threshold=5.0) == 3


def test_detect_energy_trend_reports_falling_for_recent_decline():
    from pulse.pattern_engine import DailyEnergyPoint, detect_energy_trend

    points = [
        DailyEnergyPoint(date="2026-03-18", average_energy=8.0),
        DailyEnergyPoint(date="2026-03-19", average_energy=7.0),
        DailyEnergyPoint(date="2026-03-20", average_energy=6.0),
        DailyEnergyPoint(date="2026-03-21", average_energy=5.5),
    ]

    assert detect_energy_trend(points, window=3) == "falling"


def test_estimate_ultradian_cycles_counts_sustained_90_minute_blocks():
    from pulse.pattern_engine import IntradayEnergySample, estimate_ultradian_cycles

    samples = [
        IntradayEnergySample(minute_offset=480, energy=8.0, duration_minutes=30),
        IntradayEnergySample(minute_offset=510, energy=7.5, duration_minutes=30),
        IntradayEnergySample(minute_offset=540, energy=7.2, duration_minutes=30),
        IntradayEnergySample(minute_offset=600, energy=4.0, duration_minutes=30),
        IntradayEnergySample(minute_offset=660, energy=7.1, duration_minutes=30),
        IntradayEnergySample(minute_offset=690, energy=7.0, duration_minutes=30),
        IntradayEnergySample(minute_offset=720, energy=7.2, duration_minutes=30),
    ]

    assert estimate_ultradian_cycles(samples, threshold=7.0, min_block_minutes=90) == 2


def test_estimate_ultradian_cycles_ignores_short_high_energy_spikes():
    from pulse.pattern_engine import IntradayEnergySample, estimate_ultradian_cycles

    samples = [
        IntradayEnergySample(minute_offset=480, energy=8.0, duration_minutes=30),
        IntradayEnergySample(minute_offset=510, energy=7.5, duration_minutes=30),
        IntradayEnergySample(minute_offset=540, energy=6.0, duration_minutes=30),
        IntradayEnergySample(minute_offset=600, energy=7.5, duration_minutes=30),
        IntradayEnergySample(minute_offset=630, energy=6.5, duration_minutes=30),
    ]

    assert estimate_ultradian_cycles(samples, threshold=7.0, min_block_minutes=90) == 0
