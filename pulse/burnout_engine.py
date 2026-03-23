"""Burnout score calculations for Pulse."""

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class BurnoutEntry:
    date: str
    average_energy: float
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None


@dataclass(frozen=True)
class BurnoutScoreResult:
    score: float
    ali: float
    rqs: float
    trend_penalty: float
    mbi_correction: float


def compute_burnout_score(
    entries: Sequence[BurnoutEntry],
    mbi_correction: float = 0.0,
) -> BurnoutScoreResult:
    ordered_entries = _normalize_entries(entries)
    ali = compute_allostatic_load_index(ordered_entries)
    rqs = compute_recovery_quality_score(ordered_entries)
    trend_penalty = compute_trend_penalty(ordered_entries)
    score = 100.0 - (ali * 0.5) - ((100.0 - rqs) * 0.3) - (trend_penalty * 0.2) + float(mbi_correction)
    score = _clamp(score, 0.0, 100.0)
    return BurnoutScoreResult(
        score=score,
        ali=ali,
        rqs=rqs,
        trend_penalty=trend_penalty,
        mbi_correction=float(mbi_correction),
    )


def compute_allostatic_load_index(entries: Sequence[BurnoutEntry]) -> float:
    recent_entries = list(entries)[-14:]
    if not recent_entries:
        return 0.0

    weights = _ali_weights(len(recent_entries))
    deficits = [_clamp(10.0 - entry.average_energy, 0.0, 10.0) for entry in recent_entries]
    weighted_deficit = sum(deficit * weight for deficit, weight in zip(deficits, weights))
    return weighted_deficit / sum(weights)


def compute_recovery_quality_score(entries: Sequence[BurnoutEntry]) -> float:
    recent_entries = list(entries)[-14:]
    if not recent_entries:
        return 50.0

    sleep_history: List[float] = []
    stress_history: List[float] = []
    daily_scores: List[float] = []

    for entry in recent_entries:
        sleep_hours = entry.sleep_hours
        if sleep_hours is None:
            sleep_hours = _fallback_mean(sleep_history, 7.0)
        else:
            sleep_history.append(sleep_hours)

        stress_value = _stress_score(entry.stress_level)
        if stress_value is None:
            stress_value = _fallback_mean(stress_history, 60.0)
        else:
            stress_history.append(stress_value)

        daily_scores.append((_sleep_score(sleep_hours) * 0.6) + (stress_value * 0.4))

    return _clamp(mean(daily_scores), 0.0, 100.0)


def compute_trend_penalty(entries: Sequence[BurnoutEntry]) -> float:
    recent_entries = list(entries)[-14:]
    if len(recent_entries) < 2:
        return 0.0

    current_decline = 0
    for index in range(len(recent_entries) - 1, 0, -1):
        current = recent_entries[index]
        previous = recent_entries[index - 1]
        if current.average_energy < previous.average_energy:
            current_decline += 1
        else:
            break

    if current_decline < 3:
        return 0.0
    return float((current_decline - 2) * 60)


def _normalize_entries(entries: Sequence[BurnoutEntry]) -> List[BurnoutEntry]:
    ordered_entries = list(entries)
    if not ordered_entries:
        raise ValueError("at least one burnout entry is required")
    ordered_entries.sort(key=lambda entry: entry.date)
    return ordered_entries


def _ali_weights(count: int) -> List[float]:
    if count <= 1:
        return [1.0]

    weights: List[float] = []
    for index in range(count):
        recency = (13.0 * index) / (count - 1)
        if recency <= 4.0:
            weights.append(1.0)
        elif recency >= 11.0:
            weights.append(3.0)
        else:
            weights.append(1.0 + ((recency - 4.0) * (2.0 / 7.0)))
    return weights


def _sleep_score(hours: float) -> float:
    if hours <= 4.0:
        return 0.0
    if hours >= 7.0:
        return 100.0
    return ((hours - 4.0) / 3.0) * 100.0


def _stress_score(level: Optional[str]) -> Optional[float]:
    if level is None:
        return None

    normalized = level.strip().lower()
    if normalized == "low":
        return 100.0
    if normalized == "medium":
        return 60.0
    if normalized == "high":
        return 20.0
    return 60.0


def _fallback_mean(values: Iterable[float], default: float) -> float:
    collected = list(values)
    if not collected:
        return default
    return mean(collected[-7:])


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
