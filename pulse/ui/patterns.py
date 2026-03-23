"""Patterns view-model helpers for Pulse."""

from datetime import datetime
from dataclasses import dataclass
from typing import List, Sequence

from pulse.burnout_engine import BurnoutScoreResult
from pulse.pattern_engine import DailyEnergyPoint


@dataclass(frozen=True)
class PatternCorrelation:
    label: str
    delta: float
    condition: str
    science_ref: str


@dataclass(frozen=True)
class PatternCorrelationCard:
    label: str
    summary: str
    science_ref: str


@dataclass(frozen=True)
class HeatmapCell:
    date: str
    weekday: str
    energy: float
    color: str


@dataclass(frozen=True)
class PatternsViewModel:
    heatmap_caption: str
    heatmap_cells: List[HeatmapCell]
    correlation_cards: List[PatternCorrelationCard]
    trajectory_summary: str


def build_patterns_view_model(
    daily_points: Sequence[DailyEnergyPoint],
    correlations: Sequence[PatternCorrelation],
    trajectory_scores: Sequence[BurnoutScoreResult],
) -> PatternsViewModel:
    heatmap_caption = "Heatmap covers {:d} days".format(len(daily_points))
    heatmap_cells = [build_heatmap_cell(point) for point in sorted(daily_points, key=lambda point: point.date)]
    correlation_cards = [
        PatternCorrelationCard(
            label=correlation.label,
            summary=format_correlation_summary(correlation),
            science_ref=correlation.science_ref,
        )
        for correlation in correlations
    ]
    trajectory_summary = summarize_burnout_trajectory(trajectory_scores)
    return PatternsViewModel(
        heatmap_caption=heatmap_caption,
        heatmap_cells=heatmap_cells,
        correlation_cards=correlation_cards,
        trajectory_summary=trajectory_summary,
    )


def format_correlation_summary(correlation: PatternCorrelation) -> str:
    direction = "higher" if correlation.delta >= 0 else "lower"
    return "{label}: {delta:.1f} points {direction} {condition}".format(
        label=correlation.label,
        delta=abs(correlation.delta),
        direction=direction,
        condition=correlation.condition,
    )


def summarize_burnout_trajectory(scores: Sequence[BurnoutScoreResult]) -> str:
    ordered_scores = [score.score for score in scores]
    if len(ordered_scores) < 2:
        return "Burnout score is steady"

    if _is_strictly_falling(ordered_scores):
        return "Burnout score has fallen for {:d} days".format(len(ordered_scores))
    if _is_strictly_rising(ordered_scores):
        return "Burnout score has risen for {:d} days".format(len(ordered_scores))
    return "Burnout score is moving sideways"


def build_heatmap_cell(point: DailyEnergyPoint) -> HeatmapCell:
    weekday = datetime.strptime(point.date, "%Y-%m-%d").strftime("%a")
    return HeatmapCell(
        date=point.date,
        weekday=weekday,
        energy=point.average_energy,
        color=_color_for_energy(point.average_energy),
    )


def _is_strictly_falling(values: Sequence[float]) -> bool:
    return all(current < previous for previous, current in zip(values, values[1:]))


def _is_strictly_rising(values: Sequence[float]) -> bool:
    return all(current > previous for previous, current in zip(values, values[1:]))


def _color_for_energy(energy: float) -> str:
    if energy < 4.0:
        return "#E24B4A"
    if energy < 7.0:
        return "#EF9F27"
    return "#1D9E75"
