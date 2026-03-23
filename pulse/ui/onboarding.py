"""Onboarding helpers for Pulse."""

from typing import Callable


DEFAULT_REMINDER_TIME = "20:00"
EARLIEST_REMINDER_HOUR = 18
LATEST_REMINDER_HOUR = 22


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
):
    if Gtk is None:
        return None

    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    container.set_margin_top(32)
    container.set_margin_bottom(32)
    container.set_margin_start(32)
    container.set_margin_end(32)

    hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    title = Gtk.Label(label="Pulse")
    title.set_xalign(0.0)
    title.add_css_class("title-1")
    subtitle = Gtk.Label(
        label="Track energy nightly. See burnout coming before it hits.",
        wrap=True,
        xalign=0.0,
    )
    subtitle.add_css_class("dim-label")
    hero.append(title)
    hero.append(subtitle)
    container.append(hero)

    for heading, body in (
        (
            "1. Draw the day",
            "Each evening you sketch your energy curve from 08:00 to 23:00. No forms, no hourly slots.",
        ),
        (
            "2. Build a baseline",
            "After a few days Pulse starts seeing patterns in sleep, stress, recovery, and decline streaks.",
        ),
        (
            "3. Get one direct intervention",
            "The app shows one concrete next step, not a motivational checklist.",
        ),
    ):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.add_css_class("card")
        card.set_margin_top(6)
        card.set_margin_bottom(6)
        card.set_margin_start(18)
        card.set_margin_end(18)
        heading_label = Gtk.Label(label=heading, xalign=0.0)
        heading_label.add_css_class("heading")
        body_label = Gtk.Label(label=body, wrap=True, xalign=0.0)
        body_label.add_css_class("dim-label")
        card.append(heading_label)
        card.append(body_label)
        container.append(card)

    reminder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    reminder_box.add_css_class("card")
    reminder_box.set_margin_top(12)
    reminder_box.set_margin_bottom(12)
    reminder_box.set_margin_start(18)
    reminder_box.set_margin_end(18)

    reminder_title = Gtk.Label(label="Evening reminder", xalign=0.0)
    reminder_title.add_css_class("heading")
    reminder_value = Gtk.Label(label=normalize_reminder_time(reminder_time), xalign=0.0)
    reminder_value.add_css_class("title-3")
    reminder_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 18.0, 22.0, 0.5)
    reminder_scale.set_value(_time_to_scale_value(reminder_time))
    reminder_scale.set_draw_value(False)
    reminder_scale.set_hexpand(True)

    def on_scale_changed(scale):
        reminder_value.set_text(_scale_value_to_time(scale.get_value()))

    reminder_scale.connect("value-changed", on_scale_changed)
    reminder_box.append(reminder_title)
    reminder_box.append(reminder_value)
    reminder_box.append(reminder_scale)
    container.append(reminder_box)

    start_button = Gtk.Button(label="Start")
    start_button.add_css_class("suggested-action")

    def handle_start(_button):
        on_start(_scale_value_to_time(reminder_scale.get_value()))

    start_button.connect("clicked", handle_start)
    container.append(start_button)

    scroller = Gtk.ScrolledWindow()
    scroller.set_child(container)
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    return scroller


def _time_to_scale_value(reminder_time: str) -> float:
    normalized = normalize_reminder_time(reminder_time)
    hour_text, minute_text = normalized.split(":", 1)
    return int(hour_text) + (0.5 if int(minute_text) >= 30 else 0.0)


def _scale_value_to_time(value: float) -> str:
    hour = int(value)
    minute = 30 if (value - hour) >= 0.5 else 0
    return normalize_reminder_time("{:02d}:{:02d}".format(hour, minute))
