"""Shared visual theme for Pulse GTK surfaces."""

from dataclasses import dataclass, field
from typing import Dict, Optional


SUPPORTED_THEME_MODES = ("system", "light", "dark")


@dataclass(frozen=True)
class PulseTheme:
    colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, int] = field(default_factory=dict)
    radii: Dict[str, int] = field(default_factory=dict)
    sidebar_width: int = 260


@dataclass(frozen=True)
class PageLayoutSpec:
    max_width: int
    edge_margin: int = 16


THEME = PulseTheme(
    colors={
        "bg": "#F3F4F6",
        "surface": "#FFFFFF",
        "surface_soft": "rgba(255,255,255,0.78)",
        "text": "#111827",
        "muted": "#6B7280",
        "accent": "#2F5C45",
        "accent_soft": "#D4EADC",
        "border": "rgba(17,24,39,0.08)",
    },
    spacing={
        "page": 32,
        "section": 32,
        "card": 24,
        "stack": 20,
        "compact": 12,
        "pill": 10,
    },
    radii={
        "pill": 999,
        "card": 24,
        "glass": 32,
    },
)


LIGHT_THEME_COLORS = {
    "bg": "#F3F4F6",
    "surface": "#FFFFFF",
    "surface_soft": "rgba(255,255,255,0.78)",
    "surface_glass_border": "rgba(255,255,255,0.85)",
    "text": "#111827",
    "muted": "#6B7280",
    "accent": "#2F5C45",
    "accent_soft": "#D4EADC",
    "border": "rgba(17,24,39,0.08)",
    "hover": "rgba(17,24,39,0.04)",
    "surface_border": "rgba(17,24,39,0.05)",
    "period_border": "rgba(17,24,39,0.06)",
    "bottom_bar": "rgba(243,244,246,0.92)",
    "mobile_header": "rgba(243,244,246,0.96)",
    "heatmap_grid": "rgba(255,255,255,0.68)",
    "rhythm_block": "rgba(255,255,255,0.72)",
}


DARK_THEME_COLORS = {
    "bg": "#0F172A",
    "surface": "#111827",
    "surface_soft": "rgba(15,23,42,0.82)",
    "surface_glass_border": "rgba(148,163,184,0.18)",
    "text": "#E5E7EB",
    "muted": "#94A3B8",
    "accent": "#7DD3A7",
    "accent_soft": "#163829",
    "border": "rgba(148,163,184,0.18)",
    "hover": "rgba(148,163,184,0.12)",
    "surface_border": "rgba(148,163,184,0.14)",
    "period_border": "rgba(148,163,184,0.16)",
    "bottom_bar": "rgba(15,23,42,0.94)",
    "mobile_header": "rgba(15,23,42,0.96)",
    "heatmap_grid": "rgba(15,23,42,0.72)",
    "rhythm_block": "rgba(15,23,42,0.68)",
}


HIGH_CONTRAST_LIGHT_COLORS = {
    "bg": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_soft": "#FFFFFF",
    "surface_glass_border": "#000000",
    "text": "#000000",
    "muted": "#1F1F1F",
    "accent": "#000000",
    "accent_soft": "#FFFFFF",
    "border": "#000000",
    "hover": "#D9D9D9",
    "surface_border": "#000000",
    "period_border": "#000000",
    "bottom_bar": "#FFFFFF",
    "mobile_header": "#FFFFFF",
    "heatmap_grid": "#FFFFFF",
    "rhythm_block": "#FFFFFF",
}


HIGH_CONTRAST_DARK_COLORS = {
    "bg": "#000000",
    "surface": "#000000",
    "surface_soft": "#000000",
    "surface_glass_border": "#FFFFFF",
    "text": "#FFFFFF",
    "muted": "#F2F2F2",
    "accent": "#FFFFFF",
    "accent_soft": "#000000",
    "border": "#FFFFFF",
    "hover": "#2A2A2A",
    "surface_border": "#FFFFFF",
    "period_border": "#FFFFFF",
    "bottom_bar": "#000000",
    "mobile_header": "#000000",
    "heatmap_grid": "#000000",
    "rhythm_block": "#000000",
}


PAGE_LAYOUTS = {
    "onboarding": PageLayoutSpec(max_width=1040),
    "dashboard": PageLayoutSpec(max_width=1080),
    "evening": PageLayoutSpec(max_width=960),
    "patterns": PageLayoutSpec(max_width=1120),
    "review": PageLayoutSpec(max_width=920),
    "rituals": PageLayoutSpec(max_width=820),
    "settings": PageLayoutSpec(max_width=720),
    "default": PageLayoutSpec(max_width=960),
}


def _load_ui():
    try:
        import gi

        gi.require_version("Adw", "1")
        gi.require_version("Gdk", "4.0")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Adw, Gdk, Gtk  # type: ignore

        return Gtk, Gdk, Adw
    except (ImportError, ValueError):
        return None, None, None


Gtk, Gdk, Adw = _load_ui()


def resolve_theme_palette_mode(theme_mode: str, prefer_dark: bool = False) -> str:
    normalized_mode = normalize_theme_mode(theme_mode)
    if normalized_mode != "system":
        return normalized_mode
    return "dark" if prefer_dark else "light"


def build_theme_css(theme_mode: str, prefer_dark: bool = False, high_contrast: bool = False) -> str:
    palette_mode = resolve_theme_palette_mode(theme_mode, prefer_dark=prefer_dark)
    if high_contrast:
        colors = HIGH_CONTRAST_LIGHT_COLORS if palette_mode != "dark" else HIGH_CONTRAST_DARK_COLORS
    else:
        colors = LIGHT_THEME_COLORS if palette_mode != "dark" else DARK_THEME_COLORS
    return """
.pulse-root {
  background: %(bg)s;
  color: %(text)s;
}

.pulse-sidebar {
  background: %(bg)s;
  border-right: 1px solid %(border)s;
  padding: 32px 24px;
}

.pulse-brand {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: %(text)s;
}

.pulse-subtle {
  color: %(muted)s;
}

.pulse-nav-item {
  background: transparent;
  border-radius: 999px;
  color: %(muted)s;
  padding: 10px 16px;
  border: none;
  box-shadow: none;
}

.pulse-nav-item:hover {
  background: %(hover)s;
  color: %(text)s;
}

.pulse-nav-item-active {
  background: %(accent_soft)s;
  color: %(accent)s;
}

.pulse-canvas {
  background: %(bg)s;
  padding: 20px 24px;
}

.pulse-mobile-header {
  background: %(mobile_header)s;
  border-bottom: 1px solid %(border)s;
}

.pulse-mobile-toggle {
  min-width: 40px;
  min-height: 40px;
  border-radius: 12px;
}

.pulse-card {
  background: %(surface)s;
  border-radius: 24px;
  padding: 24px;
  border: 1px solid %(surface_border)s;
}

.pulse-card-soft {
  background: %(accent_soft)s;
  border-radius: 24px;
  padding: 24px;
  color: %(accent)s;
}

.pulse-card-glass {
  background: %(surface_soft)s;
  border-radius: 32px;
  padding: 32px;
  border: 1px solid %(surface_glass_border)s;
}

.pulse-hero-title {
  font-size: 36px;
  font-weight: 500;
  letter-spacing: -1px;
  color: %(text)s;
}

.pulse-chip {
  background: %(accent_soft)s;
  color: %(accent)s;
  border-radius: 999px;
  padding: 6px 12px;
}

.pulse-review-insight-positive {
  background: #1D9E75;
  border-radius: 999px;
}

.pulse-review-insight-warning {
  background: #EF9F27;
  border-radius: 999px;
}

.pulse-review-insight-neutral {
  background: #888780;
  border-radius: 999px;
}

.pulse-heatmap-grid {
  background: %(heatmap_grid)s;
  border-radius: 20px;
  padding: 16px;
  border: 1px solid %(surface_border)s;
}

.pulse-heatmap-column-label {
  color: %(muted)s;
  font-size: 11px;
}

.pulse-heatmap-weekday {
  color: %(muted)s;
  font-size: 12px;
}

.pulse-heatmap-cell {
  min-width: 34px;
  min-height: 34px;
  border-radius: 12px;
  padding: 0;
}

.pulse-heatmap-cell label {
  font-size: 11px;
  font-weight: 600;
}

.pulse-heatmap-cell-low {
  background: #F7D7D7;
  color: #A53A39;
}

.pulse-heatmap-cell-medium {
  background: #FCE4BF;
  color: #A96C12;
}

.pulse-heatmap-cell-high {
  background: #DDE8BE;
  color: #59713A;
}

.pulse-heatmap-cell-peak {
  background: #CFE8DC;
  color: #1D6F53;
}

.pulse-heatmap-cell-missing {
  background: #EEF1F4;
  color: #B2B8C0;
}

.pulse-heatmap-legend-dot {
  min-width: 12px;
  min-height: 12px;
  border-radius: 999px;
}

.pulse-period-card {
  background: %(surface_soft)s;
  border-radius: 20px;
  padding: 18px;
  border: 1px solid %(period_border)s;
}

.pulse-period-value {
  font-size: 24px;
  font-weight: 600;
  color: %(text)s;
}

.pulse-rhythm-block {
  background: %(rhythm_block)s;
  border-radius: 18px;
  padding: 10px;
  border: 1px solid %(surface_border)s;
}

.pulse-rhythm-swatch {
  border-radius: 14px;
}

.pulse-rhythm-value {
  font-size: 18px;
  font-weight: 600;
  color: %(text)s;
}

.pulse-bottom-bar {
  background: %(bottom_bar)s;
  border-top: 1px solid %(border)s;
  padding: 4px 0;
}

.pulse-primary-button {
  min-height: 52px;
  padding: 0 20px;
  border-radius: 16px;
  font-weight: 600;
}

*:focus {
  outline: 2px solid %(accent)s;
  outline-offset: 2px;
}
""" % colors


_theme_provider: Optional[object] = None


def install_theme(display=None, theme_mode: str = "system") -> None:
    if Gtk is None or Gdk is None:
        return
    global _theme_provider
    provider = _theme_provider
    if provider is None:
        provider = Gtk.CssProvider()
        _theme_provider = provider
    target_display = display or Gdk.Display.get_default()
    if target_display is None:
        return
    prefer_dark = False
    high_contrast = False
    if Adw is not None and hasattr(Adw, "StyleManager"):
        style_manager = Adw.StyleManager.get_default()
        if style_manager is not None and hasattr(style_manager, "get_dark"):
            prefer_dark = bool(style_manager.get_dark())
        if style_manager is not None and hasattr(style_manager, "get_high_contrast"):
            high_contrast = bool(style_manager.get_high_contrast())
    provider.load_from_data(
        build_theme_css(
            theme_mode,
            prefer_dark=prefer_dark,
            high_contrast=high_contrast,
        ).encode("utf-8")
    )
    Gtk.StyleContext.add_provider_for_display(
        target_display,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def normalize_theme_mode(theme_mode: str) -> str:
    if theme_mode in SUPPORTED_THEME_MODES:
        return theme_mode
    return "system"


def apply_theme_mode(theme_mode: str) -> None:
    if Adw is None or not hasattr(Adw, "StyleManager") or not hasattr(Adw, "ColorScheme"):
        return
    style_manager = Adw.StyleManager.get_default()
    if style_manager is None:
        return

    normalized_mode = normalize_theme_mode(theme_mode)
    color_scheme = Adw.ColorScheme.DEFAULT
    if normalized_mode == "light":
        color_scheme = Adw.ColorScheme.FORCE_LIGHT
    elif normalized_mode == "dark":
        color_scheme = Adw.ColorScheme.FORCE_DARK
    style_manager.set_color_scheme(color_scheme)


def apply_classes(widget, *classes: str):
    if widget is None or not hasattr(widget, "add_css_class"):
        return widget
    for class_name in classes:
        widget.add_css_class(class_name)
    return widget


def page_layout(name: str) -> PageLayoutSpec:
    return PAGE_LAYOUTS.get(name, PAGE_LAYOUTS["default"])


def wrap_responsive(widget, max_width: int):
    if Gtk is None:
        return widget
    if Adw is not None and hasattr(Adw, "Clamp"):
        clamp = Adw.Clamp()
        clamp.set_hexpand(True)
        clamp.set_maximum_size(max_width)
        if hasattr(clamp, "set_tightening_threshold"):
            clamp.set_tightening_threshold(max(360, max_width - 160))
        clamp.set_child(widget)
        return clamp

    wrapper = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    wrapper.set_halign(Gtk.Align.CENTER)
    wrapper.set_hexpand(True)
    if hasattr(widget, "set_size_request"):
        widget.set_size_request(max_width, -1)
    wrapper.append(widget)
    return wrapper


def build_responsive_page(
    content,
    page_name: str,
    horizontal_policy=None,
    vertical_policy=None,
):
    if Gtk is None:
        return content
    layout = page_layout(page_name)
    content.set_margin_top(layout.edge_margin)
    content.set_margin_bottom(layout.edge_margin)
    content.set_margin_start(layout.edge_margin)
    content.set_margin_end(layout.edge_margin)
    content.set_hexpand(True)

    scroller = Gtk.ScrolledWindow()
    h_policy = horizontal_policy if horizontal_policy is not None else Gtk.PolicyType.AUTOMATIC
    v_policy = vertical_policy if vertical_policy is not None else Gtk.PolicyType.AUTOMATIC
    scroller.set_policy(h_policy, v_policy)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    if hasattr(scroller, "set_propagate_natural_height"):
        scroller.set_propagate_natural_height(False)
    scroller.set_child(wrap_responsive(content, layout.max_width))
    return scroller
