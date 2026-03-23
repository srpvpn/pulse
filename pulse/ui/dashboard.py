"""Dashboard helpers for Pulse."""

from dataclasses import dataclass
from typing import Optional

from pulse.advice_engine import AdviceRecommendation
from pulse.burnout_engine import BurnoutScoreResult
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
) -> DashboardViewModel:
    score_zone = score_zone_for(burnout.score)
    primary_message, primary_action, primary_science_ref = _primary_advice(score_zone, advice)
    return DashboardViewModel(
        score=burnout.score,
        score_zone=score_zone,
        primary_message=primary_message,
        primary_action=primary_action,
        primary_science_ref=primary_science_ref,
        ultradian_cycles=ultradian_cycles,
    )


def _primary_advice(
    score_zone: DashboardScoreZone,
    advice: Optional[AdviceRecommendation],
) -> tuple:
    if advice is not None:
        return advice.message, advice.action, advice.science_ref

    if score_zone.key == "red":
        return (
            "Your score is in the critical zone. Stop adding load today.",
            "Close work apps now",
            "Allostatic Load (McEwen, 1998)",
        )
    if score_zone.key == "yellow":
        return (
            "Your score is in the attention zone. Protect the next block of work.",
            "Keep the afternoon meeting-free",
            "Burnout trajectory monitoring",
        )
    return (
        "Your score is in the healthy zone. Keep the load stable.",
        "Continue with the current plan",
        "Recovery and pacing",
    )


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
    content.set_margin_top(24)
    content.set_margin_bottom(24)
    content.set_margin_start(24)
    content.set_margin_end(24)

    hero = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
    hero.add_css_class("card")
    hero.set_margin_start(12)
    hero.set_margin_end(12)
    hero.set_margin_top(6)
    hero.set_margin_bottom(6)

    ring = create_score_ring_widget(view_model.score, view_model.score_zone.color)
    if hasattr(ring, "set_content_width"):
        ring.set_content_width(180)
        ring.set_content_height(180)
    elif hasattr(ring, "set_size_request"):
        ring.set_size_request(180, 180)
    hero.append(ring)

    summary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    score_label = Gtk.Label(label="{:.0f}".format(view_model.score), xalign=0.0)
    score_label.add_css_class("title-1")
    zone_label = Gtk.Label(
        label="Burnout Score · {}".format(view_model.score_zone.label),
        xalign=0.0,
    )
    zone_label.add_css_class("heading")
    status_label = Gtk.Label(
        label=(
            "Pulse is building your baseline from fresh data."
            if not has_data
            else view_model.primary_message
        ),
        wrap=True,
        xalign=0.0,
    )
    status_label.add_css_class("dim-label")
    action_label = Gtk.Label(label=view_model.primary_action, wrap=True, xalign=0.0)
    science_label = Gtk.Label(label=view_model.primary_science_ref, wrap=True, xalign=0.0)
    science_label.add_css_class("caption")
    summary.append(score_label)
    summary.append(zone_label)
    summary.append(status_label)
    summary.append(action_label)
    summary.append(science_label)
    hero.append(summary)
    content.append(hero)

    stats_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    stats_card.add_css_class("card")
    stats_card.set_margin_start(12)
    stats_card.set_margin_end(12)
    stats_card.set_margin_top(6)
    stats_card.set_margin_bottom(6)
    stats_title = Gtk.Label(label="Today", xalign=0.0)
    stats_title.add_css_class("heading")
    cycles_label = Gtk.Label(
        label="Estimated ultradian cycles: {:d}".format(view_model.ultradian_cycles),
        xalign=0.0,
    )
    stats_card.append(stats_title)
    stats_card.append(cycles_label)
    content.append(stats_card)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_child(content)
    return scroller
