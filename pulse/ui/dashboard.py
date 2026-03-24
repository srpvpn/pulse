"""Dashboard helpers for Pulse."""

from dataclasses import dataclass
from typing import List, Optional

from pulse.advice_engine import AdviceRecommendation
from pulse.burnout_engine import BurnoutScoreResult
from pulse.i18n import tr
from pulse.ui.theme import apply_classes, build_responsive_page
from pulse.ui.widgets import create_score_ring_widget


@dataclass(frozen=True)
class DashboardScoreZone:
    key: str
    label: str
    color: str
    minimum: int
    maximum: int


@dataclass(frozen=True)
class DashboardViewModel:
    score: float
    score_zone: DashboardScoreZone
    primary_message: str
    primary_action: str
    primary_science_ref: str
    ultradian_cycles: int
    score_label: str
    zone_pill: str
    secondary_metrics: List[object]
    headline: str
    score_card_title: str
    insight_title: str
    reference_cards: List[object]


@dataclass(frozen=True)
class DashboardMetric:
    label: str
    value: str


@dataclass(frozen=True)
class DashboardReferenceCard:
    label: str
    items: List[str]


RED_ZONE = DashboardScoreZone("red", "Critical", "#E24B4A", 0, 39)
YELLOW_ZONE = DashboardScoreZone("yellow", "Attention", "#EF9F27", 40, 69)
GREEN_ZONE = DashboardScoreZone("green", "Healthy", "#1D9E75", 70, 100)


def score_zone_for(score: float) -> DashboardScoreZone:
    if score <= RED_ZONE.maximum:
        return RED_ZONE
    if score <= YELLOW_ZONE.maximum:
        return YELLOW_ZONE
    return GREEN_ZONE


def build_dashboard_view_model(
    burnout: BurnoutScoreResult,
    advice: Optional[AdviceRecommendation],
    ultradian_cycles: int = 0,
    language: str = "en",
) -> DashboardViewModel:
    score_zone = score_zone_for(burnout.score)
    primary_message, primary_action, primary_science_ref = _primary_advice(score_zone, advice, language)
    return DashboardViewModel(
        score=burnout.score,
        score_zone=score_zone,
        primary_message=primary_message,
        primary_action=primary_action,
        primary_science_ref=primary_science_ref,
        ultradian_cycles=ultradian_cycles,
        score_label="{:.0f}".format(burnout.score),
        zone_pill=tr(language, "dashboard.zone_pill", zone=score_zone.label),
        secondary_metrics=[
            DashboardMetric(label=tr(language, "dashboard.metric.rqs"), value="{:.0f}".format(burnout.rqs)),
            DashboardMetric(label=tr(language, "dashboard.metric.ali"), value="{:.1f}".format(burnout.ali)),
            DashboardMetric(label=tr(language, "dashboard.metric.cycles"), value="{:d}".format(ultradian_cycles)),
        ],
        headline=tr(language, "dashboard.headline"),
        score_card_title=tr(language, "dashboard.score_title"),
        insight_title=tr(language, "dashboard.insight_title"),
        reference_cards=[
            DashboardReferenceCard(
                label=tr(language, "dashboard.recovery_direction"),
                items=[_recovery_direction(score_zone, language)],
            ),
            DashboardReferenceCard(
                label=tr(language, "dashboard.cycles"),
                items=[tr(language, "dashboard.cycles_completed", count=ultradian_cycles)],
            ),
        ],
    )


def _primary_advice(
    score_zone: DashboardScoreZone,
    advice: Optional[AdviceRecommendation],
    language: str,
) -> tuple:
    if advice is not None:
        return advice.message, advice.action, advice.science_ref

    if score_zone.key == "red":
        return (
            tr(language, "dashboard.advice.red.message"),
            tr(language, "dashboard.advice.red.action"),
            tr(language, "dashboard.advice.red.ref"),
        )
    if score_zone.key == "yellow":
        return (
            tr(language, "dashboard.advice.yellow.message"),
            tr(language, "dashboard.advice.yellow.action"),
            tr(language, "dashboard.advice.yellow.ref"),
        )
    return (
        tr(language, "dashboard.advice.green.message"),
        tr(language, "dashboard.advice.green.action"),
        tr(language, "dashboard.advice.green.ref"),
    )


def _recovery_direction(score_zone: DashboardScoreZone, language: str) -> str:
    if score_zone.key == "green":
        return tr(language, "dashboard.load_stable")
    if score_zone.key == "yellow":
        return tr(language, "dashboard.protect_block")
    return tr(language, "dashboard.recovery_urgent")


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_ui()


def create_dashboard_page(view_model: DashboardViewModel, has_data: bool = True):
    if Gtk is None:
        return None

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

    header = Gtk.Label(label=view_model.headline, xalign=0.0)
    apply_classes(header, "pulse-hero-title")
    content.append(header)

    ring = create_score_ring_widget(view_model.score, view_model.score_zone.color)
    if hasattr(ring, "set_content_width"):
        ring.set_content_width(160)
        ring.set_content_height(160)
    elif hasattr(ring, "set_size_request"):
        ring.set_size_request(160, 160)

    hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    apply_classes(hero, "pulse-card-glass")
    hero.set_hexpand(True)
    hero_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    hero_title = Gtk.Label(label=view_model.score_card_title, xalign=0.0)
    apply_classes(hero_title, "pulse-subtle")
    hero_title.set_hexpand(True)
    zone_label = Gtk.Label(label=view_model.zone_pill, xalign=1.0)
    apply_classes(zone_label, "pulse-chip")
    hero_header.append(hero_title)
    hero_header.append(zone_label)
    hero.append(hero_header)

    hero_body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
    hero_body.append(ring)

    summary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    score_label = Gtk.Label(label=view_model.score_label, xalign=0.0)
    apply_classes(score_label, "pulse-hero-title")
    status_label = Gtk.Label(
        label=(
            "Pulse is building your baseline from fresh data."
            if not has_data
            else view_model.primary_message
        ),
        wrap=True,
        xalign=0.0,
    )
    apply_classes(status_label, "pulse-subtle")
    summary.append(score_label)
    summary.append(status_label)
    hero_body.append(summary)
    hero.append(hero_body)
    content.append(hero)

    insight = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    apply_classes(insight, "pulse-card-soft")
    insight_title = Gtk.Label(label=view_model.insight_title, xalign=0.0)
    apply_classes(insight_title, "pulse-subtle")
    insight_body = Gtk.Label(label=view_model.primary_message, wrap=True, xalign=0.0)
    apply_classes(insight_body, "pulse-brand")
    insight.append(insight_title)
    insight.append(insight_body)
    content.append(insight)

    stats_row = Gtk.FlowBox()
    stats_row.set_selection_mode(Gtk.SelectionMode.NONE)
    stats_row.set_max_children_per_line(2)
    stats_row.set_min_children_per_line(1)
    stats_row.set_column_spacing(16)
    stats_row.set_row_spacing(16)

    trend_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    apply_classes(trend_card, "pulse-card")
    trend_title = Gtk.Label(label=view_model.reference_cards[0].label, xalign=0.0)
    apply_classes(trend_title, "pulse-subtle")
    trend_card.append(trend_title)
    trend_value = Gtk.Label(label=view_model.reference_cards[0].items[0], xalign=0.0, wrap=True)
    apply_classes(trend_value, "heading")
    trend_card.append(trend_value)
    stats_row.insert(trend_card, -1)

    cycles_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    apply_classes(cycles_card, "pulse-card")
    cycles_title = Gtk.Label(label=view_model.reference_cards[1].label, xalign=0.0)
    apply_classes(cycles_title, "pulse-subtle")
    cycles_card.append(cycles_title)
    cycles_value = Gtk.Label(label=view_model.reference_cards[1].items[0], xalign=0.0, wrap=True)
    apply_classes(cycles_value, "heading")
    cycles_card.append(cycles_value)
    stats_row.insert(cycles_card, -1)
    content.append(stats_row)

    return build_responsive_page(content, "dashboard")
