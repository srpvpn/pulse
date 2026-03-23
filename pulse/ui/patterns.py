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

    direction, streak_length = _latest_monotonic_streak(ordered_scores)
    if direction == "falling":
        return "Burnout score has fallen for {:d} days".format(streak_length)
    if direction == "rising":
        return "Burnout score has risen for {:d} days".format(streak_length)
    return "Burnout score is moving sideways"


def build_heatmap_cell(point: DailyEnergyPoint) -> HeatmapCell:
    weekday = datetime.strptime(point.date, "%Y-%m-%d").strftime("%a")
    return HeatmapCell(
        date=point.date,
        weekday=weekday,
        energy=point.average_energy,
        color=_color_for_energy(point.average_energy),
    )


def _latest_monotonic_streak(values: Sequence[float]) -> tuple:
    if len(values) < 2:
        return None, 0

    direction = None
    streak_length = 0
    index = len(values) - 1

    while index > 0:
        current = values[index]
        previous = values[index - 1]
        if current == previous:
            break

        pair_direction = "rising" if current > previous else "falling"
        if direction is None:
            direction = pair_direction
        elif pair_direction != direction:
            break

        streak_length += 1
        index -= 1

    return direction, streak_length


def _color_for_energy(energy: float) -> str:
    if energy < 4.0:
        return "#E24B4A"
    if energy < 7.0:
        return "#EF9F27"
    return "#1D9E75"


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_ui()


def create_patterns_page(view_model: PatternsViewModel):
    if Gtk is None:
        return None

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    content.set_margin_top(24)
    content.set_margin_bottom(24)
    content.set_margin_start(24)
    content.set_margin_end(24)

    title = Gtk.Label(label="Patterns", xalign=0.0)
    title.add_css_class("title-2")
    content.append(title)

    heatmap_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    heatmap_card.add_css_class("card")
    heatmap_card.set_margin_start(12)
    heatmap_card.set_margin_end(12)
    heatmap_card.append(Gtk.Label(label=view_model.heatmap_caption, xalign=0.0))
    if view_model.heatmap_cells:
        for cell in view_model.heatmap_cells[-14:]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            dot = Gtk.Label()
            dot.set_markup("<span foreground='{color}'>●</span>".format(color=cell.color))
            label = Gtk.Label(
                label="{weekday} · {date} · energy {energy:.1f}".format(
                    weekday=cell.weekday,
                    date=cell.date,
                    energy=cell.energy,
                ),
                xalign=0.0,
            )
            row.append(dot)
            row.append(label)
            heatmap_card.append(row)
    else:
        empty = Gtk.Label(label="Add a few evening entries to reveal time and weekday patterns.", wrap=True, xalign=0.0)
        empty.add_css_class("dim-label")
        heatmap_card.append(empty)
    content.append(heatmap_card)

    trajectory_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    trajectory_card.add_css_class("card")
    trajectory_card.set_margin_start(12)
    trajectory_card.set_margin_end(12)
    trajectory_card.append(Gtk.Label(label="Burnout trajectory", xalign=0.0))
    trajectory_text = Gtk.Label(label=view_model.trajectory_summary, wrap=True, xalign=0.0)
    trajectory_text.add_css_class("heading")
    trajectory_card.append(trajectory_text)
    content.append(trajectory_card)

    correlation_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    correlation_card.add_css_class("card")
    correlation_card.set_margin_start(12)
    correlation_card.set_margin_end(12)
    correlation_card.append(Gtk.Label(label="Correlations", xalign=0.0))
    if view_model.correlation_cards:
        for item in view_model.correlation_cards:
            block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            label = Gtk.Label(label=item.label, xalign=0.0)
            label.add_css_class("heading")
            summary = Gtk.Label(label=item.summary, wrap=True, xalign=0.0)
            ref = Gtk.Label(label=item.science_ref, wrap=True, xalign=0.0)
            ref.add_css_class("caption")
            block.append(label)
            block.append(summary)
            block.append(ref)
            correlation_card.append(block)
    else:
        empty = Gtk.Label(label="Pulse needs a week or two of context before correlations become meaningful.", wrap=True, xalign=0.0)
        empty.add_css_class("dim-label")
        correlation_card.append(empty)
    content.append(correlation_card)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_child(content)
    return scroller
