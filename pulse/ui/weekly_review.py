"""Weekly review view-model helpers for Pulse."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MBICheckin:
    exhaustion: int
    cynicism: int
    efficacy: int


@dataclass(frozen=True)
class ScienceCard:
    title: str
    body: str
    source: str


@dataclass(frozen=True)
class WeeklyReviewViewModel:
    energy_summary: str
    mbi_correction: float
    science_card: ScienceCard


SCIENCE_CARDS: List[ScienceCard] = [
    ScienceCard(
        title="Ultradian rhythms",
        body="The brain still benefits from alternating focus and recovery blocks across the day.",
        source="Kleitman",
    ),
    ScienceCard(
        title="Psychological detachment",
        body="Switching off work after hours matters because recovery needs actual mental separation.",
        source="Sonnentag",
    ),
    ScienceCard(
        title="Allostatic load",
        body="Repeated stress without recovery accumulates and pushes baseline energy downward.",
        source="McEwen",
    ),
    ScienceCard(
        title="Sleep debt",
        body="Sleep loss compounds across days, so a single short night can distort the next week.",
        source="Walker",
    ),
    ScienceCard(
        title="Cognitive load",
        body="Too many simultaneous demands reduce the energy left for deep work and recovery.",
        source="Sweller",
    ),
    ScienceCard(
        title="Decision fatigue",
        body="Frequent choices drain the reserve that supports focus, patience, and self-control.",
        source="Baumeister",
    ),
    ScienceCard(
        title="Recovery cycles",
        body="Recovery works best when it is repeated, deliberate, and not just passive downtime.",
        source="Sonnentag",
    ),
    ScienceCard(
        title="Autonomy",
        body="Control over schedule and task order protects energy by reducing friction and pressure.",
        source="Self-determination theory",
    ),
    ScienceCard(
        title="Workload mismatch",
        body="When demand stays above capacity, burnout risk climbs even if motivation stays high.",
        source="Job demands-resources",
    ),
    ScienceCard(
        title="Attention residue",
        body="Context switching leaves residue that makes the next task feel harder than it should.",
        source="Leroy",
    ),
]


def build_weekly_review_view_model(
    this_week_average_energy: float,
    previous_week_average_energy: float,
    mbi_checkin: Optional[MBICheckin],
    week_index: int,
) -> WeeklyReviewViewModel:
    energy_summary = "Average energy {this_week:.1f} this week vs {previous_week:.1f} last week ({delta:+.1f})".format(
        this_week=this_week_average_energy,
        previous_week=previous_week_average_energy,
        delta=this_week_average_energy - previous_week_average_energy,
    )
    mbi_correction = compute_mbi_correction(mbi_checkin)
    science_card = SCIENCE_CARDS[week_index % len(SCIENCE_CARDS)]
    return WeeklyReviewViewModel(
        energy_summary=energy_summary,
        mbi_correction=mbi_correction,
        science_card=science_card,
    )


def compute_mbi_correction(mbi_checkin: Optional[MBICheckin]) -> float:
    if mbi_checkin is None:
        return 0.0

    exhaustion = _clamp(mbi_checkin.exhaustion, 0.0, 4.0)
    cynicism = _clamp(mbi_checkin.cynicism, 0.0, 4.0)
    efficacy = _clamp(mbi_checkin.efficacy, 0.0, 4.0)
    raw_score = exhaustion + cynicism + (4.0 - efficacy)
    return _clamp(-(((raw_score - 6.0) / 6.0) * 10.0), -10.0, 10.0)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_ui()


def create_weekly_review_page(view_model: WeeklyReviewViewModel):
    if Gtk is None:
        return None

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    content.set_margin_top(24)
    content.set_margin_bottom(24)
    content.set_margin_start(24)
    content.set_margin_end(24)

    title = Gtk.Label(label="Weekly Review", xalign=0.0)
    title.add_css_class("title-2")
    content.append(title)

    summary_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    summary_card.add_css_class("card")
    summary_card.set_margin_start(12)
    summary_card.set_margin_end(12)
    summary_card.append(Gtk.Label(label=view_model.energy_summary, wrap=True, xalign=0.0))
    summary_card.append(
        Gtk.Label(
            label="MBI correction this week: {:+.1f}".format(view_model.mbi_correction),
            xalign=0.0,
        )
    )
    content.append(summary_card)

    checkin_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    checkin_card.add_css_class("card")
    checkin_card.set_margin_start(12)
    checkin_card.set_margin_end(12)
    checkin_card.append(Gtk.Label(label="Maslach weekly check-in", xalign=0.0))
    preview_label = Gtk.Label(label="Move the sliders to preview this week's correction.", wrap=True, xalign=0.0)
    preview_label.add_css_class("dim-label")
    checkin_card.append(preview_label)

    scales = []
    for label_text in (
        "Exhaustion",
        "Cynicism",
        "Efficacy",
    ):
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        row.append(Gtk.Label(label=label_text, xalign=0.0))
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 4.0, 1.0)
        scale.set_draw_value(True)
        row.append(scale)
        checkin_card.append(row)
        scales.append(scale)

    preview_value = Gtk.Label(label="Preview correction: +0.0", xalign=0.0)
    preview_value.add_css_class("heading")
    checkin_card.append(preview_value)

    def update_preview(_scale):
        correction = compute_mbi_correction(
            MBICheckin(
                exhaustion=int(scales[0].get_value()),
                cynicism=int(scales[1].get_value()),
                efficacy=int(scales[2].get_value()),
            )
        )
        preview_value.set_text("Preview correction: {:+.1f}".format(correction))

    for scale in scales:
        scale.connect("value-changed", update_preview)

    content.append(checkin_card)

    science_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    science_card.add_css_class("card")
    science_card.set_margin_start(12)
    science_card.set_margin_end(12)
    title_label = Gtk.Label(label=view_model.science_card.title, xalign=0.0)
    title_label.add_css_class("heading")
    body_label = Gtk.Label(label=view_model.science_card.body, wrap=True, xalign=0.0)
    source_label = Gtk.Label(label=view_model.science_card.source, xalign=0.0)
    source_label.add_css_class("caption")
    science_card.append(title_label)
    science_card.append(body_label)
    science_card.append(source_label)
    content.append(science_card)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_child(content)
    return scroller
