"""Ritual scheduling helpers for Pulse."""
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Sequence

from pulse.i18n import tr
from pulse.ui.theme import apply_classes, build_responsive_page


@dataclass(frozen=True)
class Ritual:
    ritual_id: str
    label: str
    time: str
    active: bool = True


@dataclass(frozen=True)
class RitualItem:
    ritual_id: str
    label: str
    time: str
    active: bool


@dataclass(frozen=True)
class RitualsPageModel:
    title: str
    primary_action: str
    active_items: List[RitualItem]
    inactive_items: List[RitualItem]
    form_style: str


def due_rituals_for_time(
    rituals: Sequence[Ritual],
    current_time: str,
    delivered_ritual_ids: Sequence[str] = (),
) -> List[Ritual]:
    normalized_now = _normalize_time(current_time)
    delivered = set(delivered_ritual_ids)
    due = []
    for ritual in rituals:
        if not ritual.active:
            continue
        if ritual.ritual_id in delivered:
            continue
        if _normalize_time(ritual.time) <= normalized_now:
            due.append(_normalize_ritual(ritual))
    return sorted(due, key=lambda ritual: (_normalize_time(ritual.time), ritual.label))


def to_rituals(rows: Iterable[object]) -> List[Ritual]:
    rituals = []
    for row in rows:
        rituals.append(
            Ritual(
                ritual_id=str(row["ritual_id"]),
                label=str(row["label"]),
                time=_normalize_time(str(row["time"])),
                active=bool(row["active"]),
            )
        )
    return rituals


def _normalize_ritual(ritual: Ritual) -> Ritual:
    return Ritual(
        ritual_id=ritual.ritual_id,
        label=ritual.label,
        time=_normalize_time(ritual.time),
        active=ritual.active,
    )


def _normalize_time(time_text: str) -> str:
    text = str(time_text).strip()
    if ":" not in text:
        return "20:00"
    hour_text, minute_text = text.split(":", 1)
    try:
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return "20:00"
    hour = max(0, min(23, hour))
    minute = max(0, min(59, minute))
    return "{:02d}:{:02d}".format(hour, minute)


def build_rituals_page_model(rituals: Sequence[Ritual]) -> RitualsPageModel:
    ordered = sorted((_normalize_ritual(ritual) for ritual in rituals), key=lambda item: (item.active is False, item.time, item.label))
    active_items = [RitualItem(item.ritual_id, item.label, item.time, item.active) for item in ordered if item.active]
    inactive_items = [RitualItem(item.ritual_id, item.label, item.time, item.active) for item in ordered if not item.active]
    return RitualsPageModel(
        title="Rituals",
        primary_action="Save ritual",
        active_items=active_items,
        inactive_items=inactive_items,
        form_style="plain",
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


def create_rituals_page(
    rituals: Sequence[Ritual],
    on_save: Optional[Callable[[Ritual], None]] = None,
    language: str = "en",
):
    if Gtk is None:
        return None
    view_model = build_rituals_page_model(rituals)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

    title = Gtk.Label(label=tr(language, "rituals.title"), xalign=0.0)
    apply_classes(title, "pulse-hero-title")
    content.append(title)

    subtitle = Gtk.Label(
        label=tr(language, "rituals.subtitle"),
        wrap=True,
        xalign=0.0,
    )
    apply_classes(subtitle, "pulse-subtle")
    content.append(subtitle)

    form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    apply_classes(form, "pulse-card")
    form.append(Gtk.Label(label=tr(language, "rituals.form_title"), xalign=0.0))
    label_entry = Gtk.Entry()
    label_entry.set_placeholder_text(tr(language, "rituals.label_placeholder"))
    time_entry = Gtk.Entry()
    time_entry.set_placeholder_text("18:30")
    active_switch = Gtk.Switch()
    active_switch.set_active(True)
    active_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    active_row.append(Gtk.Label(label=tr(language, "rituals.active"), xalign=0.0))
    active_row.append(active_switch)
    save_button = Gtk.Button(label=view_model.primary_action)
    save_button.add_css_class("suggested-action")

    def handle_save(_button):
        if on_save is None:
            return
        label = label_entry.get_text().strip() or tr(language, "rituals.default_label")
        normalized_time = _normalize_time(time_entry.get_text().strip() or "20:00")
        ritual_id = label.lower().replace(" ", "-")
        on_save(
            Ritual(
                ritual_id=ritual_id,
                label=label,
                time=normalized_time,
                active=active_switch.get_active(),
            )
        )

    save_button.connect("clicked", handle_save)
    form.append(label_entry)
    form.append(time_entry)
    form.append(active_row)
    form.append(save_button)
    content.append(form)

    for block_title, items, empty_message in (
        (
            tr(language, "rituals.active_list"),
            view_model.active_items,
            tr(language, "rituals.empty_active"),
        ),
        (
            tr(language, "rituals.inactive_list"),
            view_model.inactive_items,
            tr(language, "rituals.empty_inactive"),
        ),
    ):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apply_classes(card, "pulse-card")
        heading = Gtk.Label(label=block_title, xalign=0.0)
        apply_classes(heading, "heading")
        card.append(heading)
        if items:
            for ritual in items:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                left = Gtk.Label(label=ritual.label, xalign=0.0)
                left.set_hexpand(True)
                right = Gtk.Label(label=ritual.time, xalign=1.0)
                apply_classes(right, "pulse-chip")
                row.append(left)
                row.append(right)
                card.append(row)
        else:
            empty = Gtk.Label(label=empty_message, wrap=True, xalign=0.0)
            apply_classes(empty, "pulse-subtle")
            card.append(empty)
        content.append(card)

    return build_responsive_page(content, "rituals")
