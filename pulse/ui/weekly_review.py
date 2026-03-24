"""Weekly review view-model helpers for Pulse."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Sequence

from pulse.i18n import month_label, tr
from pulse.pattern_engine import WeeklyInsight
from pulse.ui.theme import apply_classes, build_responsive_page


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
    week_title: str
    energy_summary: str
    insights: List[WeeklyInsight]
    science_card: ScienceCard
    checkin_title: str
    checkin_intro: str
    reflection_prompt: str
    save_label: str
    card_style: str


SCIENCE_CARD_KEYS = (
    "ultradian",
    "detachment",
    "allostatic",
    "sleep_debt",
    "cognitive_load",
    "decision_fatigue",
    "recovery_cycles",
    "autonomy",
    "workload_mismatch",
    "attention_residue",
)


def build_weekly_review_view_model(
    week_start: str,
    week_end: str,
    this_week_average_energy: float,
    previous_week_average_energy: float,
    insights: Sequence[WeeklyInsight],
    week_index: int,
    language: str = "en",
) -> WeeklyReviewViewModel:
    science_card = _science_card_for_week(week_index, language)
    return WeeklyReviewViewModel(
        week_title=tr(
            language,
            "review.week_title",
            start=_format_week_date(week_start, language),
            end=_format_week_date(week_end, language),
        ),
        energy_summary=_format_energy_summary(this_week_average_energy, previous_week_average_energy, language),
        insights=list(insights),
        science_card=science_card,
        checkin_title=tr(language, "review.checkin_title"),
        checkin_intro=tr(language, "review.checkin_intro"),
        reflection_prompt=tr(language, "review.reflection_prompt"),
        save_label=tr(language, "review.save"),
        card_style="plain",
    )


def compute_mbi_correction(mbi_checkin: Optional[MBICheckin]) -> float:
    if mbi_checkin is None:
        return 0.0

    exhaustion = _clamp(mbi_checkin.exhaustion, 0.0, 4.0)
    cynicism = _clamp(mbi_checkin.cynicism, 0.0, 4.0)
    efficacy = _clamp(mbi_checkin.efficacy, 0.0, 4.0)
    raw_score = exhaustion + cynicism + (4.0 - efficacy)
    return _clamp(-(((raw_score - 6.0) / 6.0) * 10.0), -10.0, 10.0)


def _format_energy_summary(this_week_average_energy: float, previous_week_average_energy: float, language: str) -> str:
    delta = this_week_average_energy - previous_week_average_energy
    if abs(delta) < 0.05:
        return tr(language, "review.energy_summary.same", energy=this_week_average_energy)
    if delta > 0:
        return tr(language, "review.energy_summary.up", energy=this_week_average_energy, delta=delta)
    return tr(language, "review.energy_summary.down", energy=this_week_average_energy, delta=abs(delta))


def _format_week_date(date_text: str, language: str) -> str:
    parsed = datetime.strptime(date_text, "%Y-%m-%d")
    if language == "ru":
        return "{day:02d} {month}".format(day=parsed.day, month=month_label(language, parsed.month))
    return "{month} {day:02d}".format(month=month_label(language, parsed.month), day=parsed.day)


def _science_card_for_week(week_index: int, language: str) -> ScienceCard:
    key = SCIENCE_CARD_KEYS[week_index % len(SCIENCE_CARD_KEYS)]
    return ScienceCard(
        title=tr(language, "review.science.{key}.title".format(key=key)),
        body=tr(language, "review.science.{key}.body".format(key=key)),
        source=tr(language, "review.science.{key}.source".format(key=key)),
    )


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


def create_weekly_review_page(
    view_model: WeeklyReviewViewModel,
    on_save: Optional[Callable[[MBICheckin, str], None]] = None,
    initial_checkin: Optional[MBICheckin] = None,
    initial_note: str = "",
    language: str = "en",
):
    if Gtk is None:
        return None

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

    header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    title = Gtk.Label(label=view_model.week_title, xalign=0.0)
    apply_classes(title, "pulse-hero-title")
    summary = Gtk.Label(label=view_model.energy_summary, wrap=True, xalign=0.0)
    apply_classes(summary, "heading")
    header.append(title)
    header.append(summary)
    content.append(header)

    insights_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    apply_classes(insights_card, "pulse-card")
    insights_title = Gtk.Label(label=tr(language, "review.insights_title"), xalign=0.0)
    apply_classes(insights_title, "heading")
    insights_card.append(insights_title)
    if view_model.insights:
        for insight in view_model.insights:
            insights_card.append(_build_insight_row(insight))
    else:
        empty = Gtk.Label(label=tr(language, "review.insights_empty"), wrap=True, xalign=0.0)
        apply_classes(empty, "pulse-subtle")
        insights_card.append(empty)
    content.append(insights_card)

    science_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    apply_classes(science_card, "pulse-card")
    science_title = Gtk.Label(label=view_model.science_card.title, xalign=0.0)
    apply_classes(science_title, "heading")
    science_body = Gtk.Label(label=view_model.science_card.body, wrap=True, xalign=0.0)
    science_source = Gtk.Label(label=view_model.science_card.source, xalign=0.0)
    apply_classes(science_source, "pulse-subtle")
    science_card.append(science_title)
    science_card.append(science_body)
    science_card.append(science_source)
    content.append(science_card)

    checkin_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    apply_classes(checkin_card, "pulse-card")
    checkin_title = Gtk.Label(label=view_model.checkin_title, xalign=0.0)
    apply_classes(checkin_title, "heading")
    checkin_intro = Gtk.Label(label=view_model.checkin_intro, wrap=True, xalign=0.0)
    apply_classes(checkin_intro, "pulse-subtle")
    checkin_card.append(checkin_title)
    checkin_card.append(checkin_intro)

    scales = []
    initial_values = initial_checkin or MBICheckin(exhaustion=0, cynicism=0, efficacy=4)
    prompts = (
        (
            tr(language, "review.exhaustion"),
            tr(language, "review.scale.exhaustion"),
            initial_values.exhaustion,
        ),
        (
            tr(language, "review.cynicism"),
            tr(language, "review.scale.cynicism"),
            initial_values.cynicism,
        ),
        (
            tr(language, "review.efficacy"),
            tr(language, "review.scale.efficacy"),
            initial_values.efficacy,
        ),
    )
    for title_text, hint_text, initial_value in prompts:
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        prompt = Gtk.Label(label=title_text, wrap=True, xalign=0.0)
        hint = Gtk.Label(label=hint_text, wrap=True, xalign=0.0)
        apply_classes(hint, "pulse-subtle")
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 4.0, 1.0)
        scale.set_draw_value(True)
        scale.set_value(initial_value)
        row.append(prompt)
        row.append(hint)
        row.append(scale)
        checkin_card.append(row)
        scales.append(scale)

    reflection_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    reflection_title = Gtk.Label(label=view_model.reflection_prompt, wrap=True, xalign=0.0)
    reflection_entry = Gtk.Entry()
    reflection_entry.set_placeholder_text(tr(language, "review.reflection_placeholder"))
    reflection_entry.set_text(initial_note or "")
    reflection_row.append(reflection_title)
    reflection_row.append(reflection_entry)
    checkin_card.append(reflection_row)

    save_button = Gtk.Button(label=view_model.save_label)
    save_button.add_css_class("suggested-action")

    def handle_save(_button):
        if on_save is None:
            return
        on_save(
            MBICheckin(
                exhaustion=int(scales[0].get_value()),
                cynicism=int(scales[1].get_value()),
                efficacy=int(scales[2].get_value()),
            ),
            reflection_entry.get_text().strip(),
        )

    save_button.connect("clicked", handle_save)
    checkin_card.append(save_button)
    content.append(checkin_card)

    return build_responsive_page(content, "review")


def _build_insight_row(insight: WeeklyInsight):
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

    stripe = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    stripe.set_size_request(6, -1)
    stripe.add_css_class(_insight_css_class(insight.type))
    row.append(stripe)

    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    title = Gtk.Label(label=insight.title, wrap=True, xalign=0.0)
    apply_classes(title, "heading")
    text = Gtk.Label(label=insight.body, wrap=True, xalign=0.0)
    body.append(title)
    body.append(text)
    row.append(body)
    return row


def _insight_css_class(insight_type: str) -> str:
    if insight_type == "positive":
        return "pulse-review-insight-positive"
    if insight_type == "warning":
        return "pulse-review-insight-warning"
    return "pulse-review-insight-neutral"
