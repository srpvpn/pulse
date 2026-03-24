"""Patterns view-model helpers for Pulse."""

from dataclasses import dataclass
from datetime import date as date_class, datetime, timedelta
from statistics import mean
from typing import Callable, List, Sequence

from pulse.burnout_engine import BurnoutScoreResult
from pulse.i18n import day_count_label, month_label, tr
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
class RhythmBlock:
    key: str
    start_date: str
    end_date: str
    label: str
    energy: float
    color: str


@dataclass(frozen=True)
class RangeOption:
    key: str
    label: str


@dataclass(frozen=True)
class PatternsViewModel:
    heatmap_caption: str
    correlation_cards: List[PatternCorrelationCard]
    trajectory_summary: str
    insight_title: str
    empty_guidance: str
    use_compact_layout: bool
    selected_range: str
    range_options: List[RangeOption]
    heatmap_layout: str
    rhythm_blocks: List[RhythmBlock]
    rhythm_summary: List[str]


RANGE_KEYS = ("7D", "30D", "90D", "1Y", "ALL")


def build_patterns_view_model(
    daily_points: Sequence[DailyEnergyPoint],
    correlations: Sequence[PatternCorrelation],
    trajectory_scores: Sequence[BurnoutScoreResult],
    selected_range: str = "30D",
    language: str = "en",
) -> PatternsViewModel:
    rhythm_blocks = build_rhythm_blocks(daily_points, selected_range=selected_range, language=language)
    heatmap_count = len(rhythm_blocks)
    correlation_cards = [
        PatternCorrelationCard(
            label=_localized_correlation_label(correlation.label, language),
            summary=format_correlation_summary(_localized_correlation(correlation, language), language=language),
            science_ref=correlation.science_ref,
        )
        for correlation in correlations
    ]
    return PatternsViewModel(
        heatmap_caption=tr(
            language,
            "patterns.heatmap_caption",
            count=heatmap_count,
            period_label=_period_label(language, selected_range, heatmap_count),
        ),
        correlation_cards=correlation_cards,
        trajectory_summary=summarize_burnout_trajectory(trajectory_scores, language=language),
        insight_title="",
        empty_guidance=tr(language, "patterns.empty"),
        use_compact_layout=True,
        selected_range=selected_range,
        range_options=[RangeOption(key=key, label=tr(language, "patterns.range.{key}".format(key=key.lower()))) for key in RANGE_KEYS],
        heatmap_layout="rhythm",
        rhythm_blocks=rhythm_blocks,
        rhythm_summary=build_rhythm_summary(rhythm_blocks, language=language),
    )


def build_rhythm_blocks(
    daily_points: Sequence[DailyEnergyPoint],
    selected_range: str = "30D",
    language: str = "en",
) -> List[RhythmBlock]:
    ordered_points = sorted(daily_points, key=lambda point: point.date)
    if not ordered_points:
        return []

    if selected_range in {"7D", "30D"}:
        return [
            RhythmBlock(
                key=point.date,
                start_date=point.date,
                end_date=point.date,
                label=_format_day_label(_parse_date(point.date), language),
                energy=point.average_energy,
                color=_color_for_energy(point.average_energy),
            )
            for point in ordered_points
        ]

    groups = {}
    for point in ordered_points:
        key, label, start_date, end_date = _grouping_for_point(point.date, selected_range, language)
        groups.setdefault(key, {"label": label, "start_date": start_date, "end_date": end_date, "values": []})
        groups[key]["values"].append(point.average_energy)

    blocks = []
    for key in sorted(groups):
        group = groups[key]
        energy = mean(group["values"])
        blocks.append(
            RhythmBlock(
                key=key,
                start_date=group["start_date"],
                end_date=group["end_date"],
                label=group["label"],
                energy=energy,
                color=_color_for_energy(energy),
            )
        )
    return blocks


def build_rhythm_summary(
    rhythm_blocks: Sequence[RhythmBlock],
    language: str = "en",
) -> List[str]:
    if not rhythm_blocks:
        return []

    average_energy = mean(block.energy for block in rhythm_blocks)
    best_block = max(rhythm_blocks, key=lambda block: block.energy)
    lowest_block = min(rhythm_blocks, key=lambda block: block.energy)
    first_energy = rhythm_blocks[0].energy
    last_energy = rhythm_blocks[-1].energy
    delta = last_energy - first_energy

    summary = [
        tr(language, "patterns.rhythm.average", energy=average_energy),
        tr(language, "patterns.rhythm.best_worst", best=best_block.label, worst=lowest_block.label),
    ]
    if abs(delta) < 0.15:
        summary.append(tr(language, "patterns.rhythm.flat"))
    elif delta > 0:
        summary.append(tr(language, "patterns.rhythm.ending_higher", delta=abs(delta)))
    else:
        summary.append(tr(language, "patterns.rhythm.ending_lower", delta=abs(delta)))
    return summary


def format_correlation_summary(correlation: PatternCorrelation, language: str = "en") -> str:
    direction = tr(language, "patterns.direction.higher") if correlation.delta >= 0 else tr(language, "patterns.direction.lower")
    return tr(
        language,
        "patterns.correlation.summary",
        label=correlation.label,
        delta=abs(correlation.delta),
        direction=direction,
        condition=correlation.condition,
    )


def summarize_burnout_trajectory(scores: Sequence[BurnoutScoreResult], language: str = "en") -> str:
    ordered_scores = [score.score for score in scores]
    if len(ordered_scores) < 2:
        return tr(language, "patterns.trajectory.steady")

    direction, streak_length = _latest_monotonic_streak(ordered_scores)
    if direction == "falling":
        return tr(language, "patterns.trajectory.falling", count=streak_length, day_label=day_count_label(language, streak_length))
    if direction == "rising":
        return tr(language, "patterns.trajectory.rising", count=streak_length, day_label=day_count_label(language, streak_length))
    return tr(language, "patterns.trajectory.sideways")


def _grouping_for_point(date_text: str, selected_range: str, language: str):
    parsed = _parse_date(date_text)
    if selected_range == "90D":
        week_start = parsed - timedelta(days=parsed.weekday())
        week_end = week_start + timedelta(days=6)
        return (
            week_start.isoformat(),
            _format_day_label(week_start, language),
            week_start.isoformat(),
            week_end.isoformat(),
        )
    month_start = parsed.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    return (
        month_start.strftime("%Y-%m"),
        _format_month_label(month_start, language),
        month_start.isoformat(),
        month_end.isoformat(),
    )


def _format_day_label(value: date_class, language: str) -> str:
    if language == "ru":
        return "{day} {month}".format(day=value.day, month=month_label(language, value.month))
    return "{month} {day}".format(month=month_label(language, value.month), day=value.day)


def _format_month_label(value: date_class, language: str) -> str:
    label = month_label(language, value.month)
    return label.capitalize() if language == "en" else label


def _period_label(language: str, selected_range: str, count: int) -> str:
    plurality = "one" if count == 1 else "many"
    if selected_range in {"7D", "30D"}:
        return tr(language, "patterns.period.daily.{plurality}".format(plurality=plurality))
    if selected_range == "90D":
        return tr(language, "patterns.period.weekly.{plurality}".format(plurality=plurality))
    return tr(language, "patterns.period.monthly.{plurality}".format(plurality=plurality))


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
    if energy < 6.0:
        return "#EF9F27"
    if energy < 8.0:
        return "#93B75D"
    return "#1D9E75"


def _localized_correlation(correlation: PatternCorrelation, language: str) -> PatternCorrelation:
    return PatternCorrelation(
        label=_localized_correlation_label(correlation.label, language),
        delta=correlation.delta,
        condition=_localized_correlation_condition(correlation.condition, language),
        science_ref=correlation.science_ref,
    )


def _localized_correlation_label(label: str, language: str) -> str:
    mapping = {
        "Sleep vs next-day energy": "patterns.correlation.sleep.label",
        "Activity vs energy": "patterns.correlation.activity.label",
        "Stress vs energy": "patterns.correlation.stress.label",
    }
    key = mapping.get(label)
    return tr(language, key) if key else label


def _localized_correlation_condition(condition: str, language: str) -> str:
    mapping = {
        "after 7+ hours of sleep": "patterns.correlation.sleep.condition",
        "on days with movement": "patterns.correlation.activity.condition",
        "on low-stress days": "patterns.correlation.stress.condition",
    }
    key = mapping.get(condition)
    return tr(language, key) if key else condition


def _parse_date(value: str) -> date_class:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_ui()


def create_patterns_page(
    view_model: PatternsViewModel,
    on_select_range: Callable[[str], None] = None,
    language: str = "en",
):
    if Gtk is None:
        return None
    from pulse.ui.theme import apply_classes, build_responsive_page

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

    header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    title = Gtk.Label(label=view_model.insight_title or tr(language, "patterns.title"), xalign=0.0)
    apply_classes(title, "pulse-hero-title")
    header.append(title)

    range_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    for option in view_model.range_options:
        button = Gtk.Button(label=option.label)
        apply_classes(button, "pulse-nav-item")
        if option.key == view_model.selected_range:
            button.add_css_class("suggested-action")
            button.set_sensitive(False)
        if on_select_range is not None:
            button.connect("clicked", lambda _button, key: on_select_range(key), option.key)
        range_row.append(button)
    header.append(range_row)
    content.append(header)

    rhythm_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    apply_classes(rhythm_card, "pulse-card")
    rhythm_title = Gtk.Label(label=view_model.heatmap_caption, xalign=0.0)
    apply_classes(rhythm_title, "heading")
    rhythm_card.append(rhythm_title)
    if view_model.rhythm_blocks:
        rhythm_card.append(_build_rhythm_card(view_model, language=language))
    else:
        empty = Gtk.Label(label=view_model.empty_guidance, wrap=True, xalign=0.0)
        apply_classes(empty, "pulse-subtle")
        rhythm_card.append(empty)
    content.append(rhythm_card)

    lower_stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)

    trajectory_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    apply_classes(trajectory_card, "pulse-card")
    trajectory_card.append(Gtk.Label(label=tr(language, "patterns.trajectory"), xalign=0.0))
    trajectory_text = Gtk.Label(label=view_model.trajectory_summary, wrap=True, xalign=0.0)
    apply_classes(trajectory_text, "heading")
    trajectory_card.append(trajectory_text)

    correlation_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    apply_classes(correlation_card, "pulse-card")
    correlation_card.append(Gtk.Label(label=tr(language, "patterns.correlations"), xalign=0.0))
    if view_model.correlation_cards:
        for item in view_model.correlation_cards:
            block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            label = Gtk.Label(label=item.label, xalign=0.0)
            label.add_css_class("heading")
            summary = Gtk.Label(label=item.summary, wrap=True, xalign=0.0)
            ref = Gtk.Label(label=item.science_ref, wrap=True, xalign=0.0)
            apply_classes(ref, "pulse-subtle")
            block.append(label)
            block.append(summary)
            block.append(ref)
            correlation_card.append(block)
    else:
        empty = Gtk.Label(label=view_model.empty_guidance, wrap=True, xalign=0.0)
        apply_classes(empty, "pulse-subtle")
        correlation_card.append(empty)

    lower_stack.append(trajectory_card)
    lower_stack.append(correlation_card)
    content.append(lower_stack)
    return build_responsive_page(content, "patterns")


def _build_rhythm_card(view_model: PatternsViewModel, language: str = "en"):
    layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

    summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    summary_title = Gtk.Label(label=tr(language, "patterns.summary.title"), xalign=0.0)
    summary_title.add_css_class("heading")
    summary_box.append(summary_title)
    for line in view_model.rhythm_summary:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bullet = Gtk.Label(label="•", xalign=0.0)
        text = Gtk.Label(label=line, wrap=True, xalign=0.0)
        row.append(bullet)
        row.append(text)
        summary_box.append(row)
    layout.append(summary_box)

    strip_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    strip = Gtk.FlowBox()
    strip.set_selection_mode(Gtk.SelectionMode.NONE)
    strip.set_column_spacing(10)
    strip.set_row_spacing(10)
    strip.set_max_children_per_line(10)
    strip.set_min_children_per_line(6)
    for block in view_model.rhythm_blocks:
        strip.insert(_build_rhythm_block(block), -1)
    strip_wrap.append(strip)
    strip_wrap.append(_build_heatmap_legend(language=language))
    layout.append(strip_wrap)
    return layout


def _build_rhythm_block(block: RhythmBlock):
    from pulse.ui.theme import apply_classes

    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    card.set_size_request(74, -1)
    apply_classes(card, "pulse-rhythm-block")

    swatch = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    swatch.set_size_request(74, 54)
    apply_classes(swatch, "pulse-rhythm-swatch", _css_class_for_color(block.color))

    value = Gtk.Label(label="{:.1f}".format(block.energy), xalign=0.0)
    apply_classes(value, "pulse-rhythm-value")
    label = Gtk.Label(label=block.label, wrap=True, xalign=0.0)
    apply_classes(label, "pulse-subtle")

    swatch.set_tooltip_text("{start} · {energy:.1f}".format(start=block.start_date, energy=block.energy))
    card.append(swatch)
    card.append(value)
    card.append(label)
    return card


def _build_heatmap_legend(language: str = "en"):
    from pulse.ui.theme import apply_classes

    legend = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    legend.set_halign(Gtk.Align.START)
    for text, css_class in (
        (tr(language, "patterns.legend.low"), "pulse-heatmap-cell-low"),
        (tr(language, "patterns.legend.medium"), "pulse-heatmap-cell-medium"),
        (tr(language, "patterns.legend.high"), "pulse-heatmap-cell-high"),
        (tr(language, "patterns.legend.peak"), "pulse-heatmap-cell-peak"),
    ):
        item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dot = Gtk.Box()
        dot.set_size_request(12, 12)
        apply_classes(dot, "pulse-heatmap-legend-dot", css_class)
        label = Gtk.Label(label=text, xalign=0.0)
        apply_classes(label, "pulse-subtle")
        item.append(dot)
        item.append(label)
        legend.append(item)
    return legend


def _css_class_for_color(color: str) -> str:
    mapping = {
        "#E24B4A": "pulse-heatmap-cell-low",
        "#EF9F27": "pulse-heatmap-cell-medium",
        "#93B75D": "pulse-heatmap-cell-high",
        "#1D9E75": "pulse-heatmap-cell-peak",
    }
    return mapping.get(color, "pulse-heatmap-cell-high")
