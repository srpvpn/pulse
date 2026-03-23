"""Evening input helpers for Pulse."""

from dataclasses import dataclass
from typing import List, Sequence


DAY_START_HOUR = 8
DAY_END_HOUR = 23


@dataclass(frozen=True)
class CurvePoint:
    minute_offset: int
    level: float


@dataclass(frozen=True)
class HourlyEnergySample:
    hour: int
    level: float


def sample_energy_curve(
    curve_points: Sequence[CurvePoint],
    start_hour: int = DAY_START_HOUR,
    end_hour: int = DAY_END_HOUR,
) -> List[HourlyEnergySample]:
    points = _sort_points(curve_points)
    if not points:
        return []

    hourly_samples = []
    for hour in range(start_hour, end_hour + 1):
        minute_offset = (hour - start_hour) * 60
        level = _sample_level_at(points, minute_offset)
        hourly_samples.append(HourlyEnergySample(hour=hour, level=level))
    return hourly_samples


def _sort_points(curve_points: Sequence[CurvePoint]) -> List[CurvePoint]:
    points = list(curve_points)
    for index, point in enumerate(points):
        points[index] = CurvePoint(
            minute_offset=int(point.minute_offset),
            level=_sanitize_level(point.level),
        )
    points.sort(key=lambda point: point.minute_offset)
    return points


def _sample_level_at(points: Sequence[CurvePoint], minute_offset: int) -> float:
    if minute_offset <= points[0].minute_offset:
        return points[0].level
    if minute_offset >= points[-1].minute_offset:
        return points[-1].level

    for left, right in zip(points, points[1:]):
        if left.minute_offset <= minute_offset <= right.minute_offset:
            return _interpolate(left, right, minute_offset)

    return points[-1].level


def _interpolate(left: CurvePoint, right: CurvePoint, minute_offset: int) -> float:
    span = right.minute_offset - left.minute_offset
    if span <= 0:
        return right.level
    position = (minute_offset - left.minute_offset) / float(span)
    return left.level + ((right.level - left.level) * position)


def _sanitize_level(level: object) -> float:
    try:
        value = float(level)
    except (TypeError, ValueError):
        value = 1.0
    return max(1.0, min(10.0, value))
