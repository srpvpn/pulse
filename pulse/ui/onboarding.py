"""Onboarding helpers for Pulse."""

from dataclasses import dataclass
from typing import Callable

from pulse.i18n import tr
from pulse.ui.theme import apply_classes, build_responsive_page


DEFAULT_REMINDER_TIME = "20:00"
EARLIEST_REMINDER_HOUR = 18
LATEST_REMINDER_HOUR = 22
ONBOARDING_CTA_LABEL = "Start tracking tonight"
ONBOARDING_STEPS = (
    (
        "Draw the day",
        "Sketch your energy from 08:00 to 23:00 in one pass instead of filling a rigid form.",
    ),
    (
        "See the baseline",
        "Pulse uses a few evenings of data to estimate burnout risk, decline streaks, and recovery signals.",
    ),
    (
        "Act early",
        "The app surfaces one direct next move and keeps rituals visible before your week starts to slip.",
    ),
)


@dataclass(frozen=True)
class OnboardingPageModel:
    headline: str
    subheadline: str
    badge: str
    reminder_title: str
    feature_columns: int


def build_onboarding_page_model(reminder_time: str, language: str = "en") -> OnboardingPageModel:
    return OnboardingPageModel(
        headline=tr(language, "onboarding.headline"),
        subheadline=tr(language, "onboarding.subheadline"),
        badge=tr(language, "onboarding.badge"),
        reminder_title=tr(language, "onboarding.reminder_title"),
        feature_columns=3,
    )


def normalize_reminder_time(reminder_time):
    text = str(reminder_time).strip()
    if not text:
        return DEFAULT_REMINDER_TIME
    if ":" not in text:
        return DEFAULT_REMINDER_TIME
    hour_text, minute_text = text.split(":", 1)
    try:
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return DEFAULT_REMINDER_TIME
    if hour < EARLIEST_REMINDER_HOUR or hour > LATEST_REMINDER_HOUR:
        return DEFAULT_REMINDER_TIME
    if hour == LATEST_REMINDER_HOUR and minute > 0:
        return DEFAULT_REMINDER_TIME
    if minute < 0 or minute > 59:
        return DEFAULT_REMINDER_TIME
    return "{:02d}:{:02d}".format(hour, minute)


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, Gtk  # type: ignore

        return Gtk, Adw
    except (ImportError, ValueError):
        return None, None


Gtk, Adw = _load_ui()


def create_onboarding_page(
    reminder_time: str,
    on_start: Callable[[str], None],
    language: str = "en",
):
    if Gtk is None:
        return None
    view_model = build_onboarding_page_model(reminder_time, language=language)

    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    apply_classes(container, "pulse-root")

    hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    apply_classes(hero_card, "pulse-card-glass")
    title = Gtk.Label(label=tr(language, "app.name"), xalign=0.0)
    apply_classes(title, "pulse-brand")
    headline = Gtk.Label(label=view_model.headline, xalign=0.0)
    apply_classes(headline, "pulse-hero-title")
    subtitle = Gtk.Label(label=view_model.subheadline, wrap=True, xalign=0.0)
    apply_classes(subtitle, "pulse-subtle")
    badge = Gtk.Label(label=view_model.badge, xalign=0.0)
    apply_classes(badge, "pulse-chip")
    hero_card.append(title)
    hero_card.append(headline)
    hero_card.append(subtitle)
    hero_card.append(badge)
    container.append(hero_card)

    reminder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    apply_classes(reminder_box, "pulse-card")
    reminder_title = Gtk.Label(label=view_model.reminder_title, xalign=0.0)
    apply_classes(reminder_title, "heading")
    reminder_value = Gtk.Label(label=normalize_reminder_time(reminder_time), xalign=0.0)
    apply_classes(reminder_value, "pulse-hero-title")
    reminder_hint = Gtk.Label(
        label=tr(language, "onboarding.reminder_hint"),
        wrap=True,
        xalign=0.0,
    )
    apply_classes(reminder_hint, "pulse-subtle")
    reminder_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 18.0, 22.0, 0.5)
    reminder_scale.set_value(_time_to_scale_value(reminder_time))
    reminder_scale.set_draw_value(False)
    reminder_scale.set_hexpand(True)

    def on_scale_changed(scale):
        reminder_value.set_text(_scale_value_to_time(scale.get_value()))

    reminder_scale.connect("value-changed", on_scale_changed)
    reminder_box.append(reminder_title)
    reminder_box.append(reminder_value)
    reminder_box.append(reminder_hint)
    reminder_box.append(reminder_scale)
    container.append(reminder_box)

    cards_row = Gtk.FlowBox()
    cards_row.set_selection_mode(Gtk.SelectionMode.NONE)
    cards_row.set_max_children_per_line(3)
    cards_row.set_min_children_per_line(1)
    cards_row.set_column_spacing(16)
    cards_row.set_row_spacing(16)
    for index, (heading, body) in enumerate(ONBOARDING_STEPS, start=1):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apply_classes(card, "pulse-card")
        card.set_hexpand(True)
        heading_label = Gtk.Label(label=tr(language, "onboarding.step{}.title".format(index)), xalign=0.0)
        apply_classes(heading_label, "heading")
        body_label = Gtk.Label(label=tr(language, "onboarding.step{}.body".format(index)), wrap=True, xalign=0.0)
        apply_classes(body_label, "pulse-subtle")
        card.append(heading_label)
        card.append(body_label)
        cards_row.insert(card, -1)
    container.append(cards_row)

    start_button = Gtk.Button(label=tr(language, "onboarding.start"))
    start_button.add_css_class("suggested-action")
    start_button.set_halign(Gtk.Align.START)
    start_button.set_margin_top(8)

    def handle_start(_button):
        on_start(_scale_value_to_time(reminder_scale.get_value()))

    start_button.connect("clicked", handle_start)
    container.append(start_button)

    return build_responsive_page(container, "onboarding")


def _time_to_scale_value(reminder_time: str) -> float:
    normalized = normalize_reminder_time(reminder_time)
    hour_text, minute_text = normalized.split(":", 1)
    return int(hour_text) + (0.5 if int(minute_text) >= 30 else 0.0)


def _scale_value_to_time(value: float) -> str:
    hour = int(value)
    minute = 30 if (value - hour) >= 0.5 else 0
    return normalize_reminder_time("{:02d}:{:02d}".format(hour, minute))
