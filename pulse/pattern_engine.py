"""Pattern detection helpers for Pulse."""

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, stdev
from typing import List, Optional, Sequence

from pulse.i18n import tr, weekday_label


@dataclass(frozen=True)
class DailyEnergyPoint:
    date: str
    average_energy: float


@dataclass(frozen=True)
class IntradayEnergySample:
    minute_offset: int
    energy: float
    duration_minutes: int = 30


@dataclass(frozen=True)
class WeeklyInsightDay:
    date: str
    avg_energy: float
    sleep_hours: Optional[float] = None
    physical_activity: Optional[str] = None


@dataclass(frozen=True)
class WeeklyInsight:
    title: str
    body: str
    type: str


def count_consecutive_low_energy_days(
    points: Sequence[DailyEnergyPoint],
    threshold: float = 5.0,
) -> int:
    ordered_points = _sort_points(points)
    streak = 0
    for point in reversed(ordered_points):
        if point.average_energy < threshold:
            streak += 1
            continue
        break
    return streak


def detect_energy_trend(
    points: Sequence[DailyEnergyPoint],
    window: int = 3,
) -> str:
    ordered_points = _sort_points(points)
    if window <= 1 or len(ordered_points) < window:
        return "flat"

    recent_points = ordered_points[-window:]
    start = recent_points[0].average_energy
    end = recent_points[-1].average_energy

    if end < start - 0.5:
        return "falling"
    if end > start + 0.5:
        return "rising"
    return "flat"


def estimate_ultradian_cycles(
    samples: Sequence[IntradayEnergySample],
    threshold: float = 7.0,
    min_block_minutes: int = 90,
) -> int:
    ordered_samples = _sort_intraday_samples(samples)
    if not ordered_samples:
        return 0

    cycles = 0
    current_block_minutes = 0
    expected_offset = None

    for sample in ordered_samples:
        if sample.energy >= threshold and (
            expected_offset is None or sample.minute_offset == expected_offset
        ):
            current_block_minutes += sample.duration_minutes
        else:
            cycles += current_block_minutes // min_block_minutes
            current_block_minutes = sample.duration_minutes if sample.energy >= threshold else 0

        expected_offset = sample.minute_offset + sample.duration_minutes

        if sample.energy < threshold:
            expected_offset = None

    cycles += current_block_minutes // min_block_minutes
    return cycles


def generate_weekly_insights(
    week_data: Sequence[WeeklyInsightDay],
    historical_data: Optional[Sequence[WeeklyInsightDay]] = None,
    language: str = "en",
) -> List[WeeklyInsight]:
    ordered_days = sorted(week_data, key=lambda day: day.date)
    if not ordered_days:
        return []

    candidates = []

    best_day = max(ordered_days, key=lambda day: day.avg_energy)
    worst_day = min(ordered_days, key=lambda day: day.avg_energy)
    candidates.append(
        (
            60,
            WeeklyInsight(
                title="Best vs worst day",
                body=(
                    "Best day was {best}, worst day was {worst}. Gap {gap:.1f} points."
                ),
                type="neutral",
            ),
        )
    )
    candidates[-1] = (
        60,
        WeeklyInsight(
            title=tr(language, "weekly_insight.best_worst.title"),
            body=tr(
                language,
                "weekly_insight.best_worst.body",
                best=_weekday_name(best_day.date, language),
                worst=_weekday_name(worst_day.date, language),
                gap=best_day.avg_energy - worst_day.avg_energy,
            ),
            type="neutral",
        ),
    )

    if len(ordered_days) >= 2:
        volatility = stdev(day.avg_energy for day in ordered_days)
        if volatility < 1.0:
            candidates.append(
                (
                    50,
                    WeeklyInsight(
                        title=tr(language, "weekly_insight.stable.title"),
                        body=tr(language, "weekly_insight.stable.body"),
                        type="positive",
                    ),
                )
            )
        elif volatility > 2.5:
            candidates.append(
                (
                    80,
                    WeeklyInsight(
                        title=tr(language, "weekly_insight.volatile.title"),
                        body=tr(language, "weekly_insight.volatile.body"),
                        type="warning",
                    ),
                )
            )

    sleep_values = [day.sleep_hours for day in ordered_days if day.sleep_hours is not None]
    if sleep_values:
        avg_sleep = mean(sleep_values)
        if avg_sleep < 6.5:
            candidates.append(
                (
                    90,
                    WeeklyInsight(
                        title=tr(language, "weekly_insight.sleep.title"),
                        body=tr(language, "weekly_insight.sleep.body", hours=avg_sleep),
                        type="warning",
                    ),
                )
            )

    active_days = sum(
        1
        for day in ordered_days
        if (day.physical_activity or "").strip().lower() in {"yes", "some"}
    )
    if active_days >= 4:
        candidates.append(
            (
                70,
                WeeklyInsight(
                    title=tr(language, "weekly_insight.activity_positive.title"),
                    body=tr(language, "weekly_insight.activity_positive.body", count=active_days),
                    type="positive",
                ),
            )
        )
    elif active_days == 0:
        candidates.append(
            (
                40,
                WeeklyInsight(
                    title=tr(language, "weekly_insight.activity_neutral.title"),
                    body=tr(language, "weekly_insight.activity_neutral.body"),
                    type="neutral",
                ),
            )
        )

    if _is_declining_tail(ordered_days[-3:]):
        candidates.append(
            (
                100,
                WeeklyInsight(
                    title=tr(language, "weekly_insight.drop.title"),
                    body=tr(language, "weekly_insight.drop.body"),
                    type="warning",
                ),
            )
        )

    historical_insight = _historical_weekday_insight(ordered_days, historical_data or [], language)
    if historical_insight is not None:
        candidates.append((65, historical_insight))

    candidates.sort(key=lambda item: (-item[0], item[1].title))
    return [insight for _, insight in candidates[:3]]


def _sort_points(points: Sequence[DailyEnergyPoint]) -> List[DailyEnergyPoint]:
    ordered_points = list(points)
    ordered_points.sort(key=lambda point: point.date)
    return ordered_points


def _sort_intraday_samples(
    samples: Sequence[IntradayEnergySample],
) -> List[IntradayEnergySample]:
    ordered_samples = list(samples)
    ordered_samples.sort(key=lambda sample: sample.minute_offset)
    return ordered_samples


def _is_declining_tail(days: Sequence[WeeklyInsightDay]) -> bool:
    if len(days) < 3:
        return False
    return all(current.avg_energy < previous.avg_energy for previous, current in zip(days, days[1:]))


def _weekday_name(date_text: str, language: str = "en") -> str:
    weekday_index = datetime.strptime(date_text, "%Y-%m-%d").weekday()
    return weekday_label(language, weekday_index, abbreviated=False)


def _historical_weekday_insight(
    week_data: Sequence[WeeklyInsightDay],
    historical_data: Sequence[WeeklyInsightDay],
    language: str = "en",
) -> Optional[WeeklyInsight]:
    if len(_distinct_weeks(historical_data)) < 3:
        return None

    history_by_weekday = {}
    for day in historical_data:
        weekday = _weekday_name(day.date, language)
        history_by_weekday.setdefault(weekday, []).append(day.avg_energy)

    deltas = []
    for day in week_data:
        weekday = _weekday_name(day.date, language)
        baseline = history_by_weekday.get(weekday)
        if not baseline:
            continue
        deltas.append((weekday, day.avg_energy - mean(baseline)))

    if not deltas:
        return None

    weekday, delta = min(deltas, key=lambda item: item[1])
    if delta >= -0.5:
        return None

    return WeeklyInsight(
        title=tr(language, "weekly_insight.baseline.title"),
        body=tr(language, "weekly_insight.baseline.body", weekday=weekday, delta=abs(delta)),
        type="warning",
    )


def _distinct_weeks(days: Sequence[WeeklyInsightDay]) -> set:
    return {
        datetime.strptime(day.date, "%Y-%m-%d").isocalendar()[:2]
        for day in days
    }
