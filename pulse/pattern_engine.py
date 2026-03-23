"""Pattern detection helpers for Pulse."""

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class DailyEnergyPoint:
    date: str
    average_energy: float


@dataclass(frozen=True)
class IntradayEnergySample:
    minute_offset: int
    energy: float
    duration_minutes: int = 30


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
