"""Settings page for Pulse."""

from dataclasses import dataclass
from typing import Callable

from pulse.i18n import tr
from pulse.ui.theme import apply_classes, build_responsive_page


@dataclass(frozen=True)
class SettingsPageModel:
    title: str
    language_title: str
    current_language: str
    language_options: tuple
    theme_title: str
    current_theme_mode: str
    theme_options: tuple


def build_settings_page_model(language: str, theme_mode: str) -> SettingsPageModel:
    return SettingsPageModel(
        title=tr(language, "settings.title"),
        language_title=tr(language, "settings.language_title"),
        current_language=language,
        language_options=(
            ("en", tr(language, "language.english")),
            ("ru", tr(language, "language.russian")),
            ("it", tr(language, "language.italian")),
        ),
        theme_title=tr(language, "settings.theme_title"),
        current_theme_mode=theme_mode,
        theme_options=(
            ("system", tr(language, "settings.theme.system")),
            ("light", tr(language, "settings.theme.light")),
            ("dark", tr(language, "settings.theme.dark")),
        ),
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


def create_settings_page(
    language: str,
    theme_mode: str,
    on_language_change: Callable[[str], None],
    on_theme_change: Callable[[str], None],
):
    if Gtk is None:
        return None
    view_model = build_settings_page_model(language, theme_mode)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

    title = Gtk.Label(label=view_model.title, xalign=0.0)
    apply_classes(title, "pulse-hero-title")
    content.append(title)

    content.append(
        _build_choice_card(
            section_title=view_model.language_title,
            options=view_model.language_options,
            current_value=view_model.current_language,
            on_change=on_language_change,
        )
    )
    content.append(
        _build_choice_card(
            section_title=view_model.theme_title,
            options=view_model.theme_options,
            current_value=view_model.current_theme_mode,
            on_change=on_theme_change,
        )
    )

    return build_responsive_page(content, "settings")


def _build_choice_card(section_title: str, options: tuple, current_value: str, on_change: Callable[[str], None]):
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    apply_classes(card, "pulse-card")

    subtitle = Gtk.Label(label=section_title, xalign=0.0)
    apply_classes(subtitle, "heading")
    card.append(subtitle)

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    buttons = []

    def handle_click(button, value):
        for other in buttons:
            if hasattr(other, "remove_css_class"):
                other.remove_css_class("suggested-action")
            other.set_sensitive(True)
        button.add_css_class("suggested-action")
        button.set_sensitive(False)
        on_change(value)

    for value, label in options:
        button = Gtk.Button(label=label)
        apply_classes(button, "pulse-nav-item")
        if value == current_value:
            button.add_css_class("suggested-action")
            button.set_sensitive(False)
        button.connect("clicked", handle_click, value)
        buttons.append(button)
        row.append(button)

    card.append(row)
    return card
