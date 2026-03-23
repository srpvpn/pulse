"""Widget helpers for Pulse."""

import math
from dataclasses import dataclass
from typing import Optional


def _load_gtk():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_gtk()


@dataclass
class ScoreRingWidget:
    score: float = 0.0
    zone_color: str = "#1D9E75"

    def present(self) -> None:
        return None

    def set_score(self, score: float, zone_color: Optional[str] = None) -> None:
        self.score = score
        if zone_color is not None:
            self.zone_color = zone_color


def _draw_score_ring(widget, context, width, height) -> None:
    size = min(width, height)
    radius = max((size / 2.0) - 8.0, 1.0)
    center_x = width / 2.0
    center_y = height / 2.0
    start_angle = -math.pi / 2.0
    score_ratio = max(0.0, min(getattr(widget, "score", 0.0) / 100.0, 1.0))
    end_angle = start_angle + (2.0 * math.pi * score_ratio)

    if hasattr(context, "set_line_width"):
        context.set_line_width(8.0)

    if hasattr(context, "set_source_rgba"):
        context.set_source_rgba(0.2, 0.2, 0.2, 0.2)
    if hasattr(context, "arc"):
        context.arc(center_x, center_y, radius, 0.0, 2.0 * math.pi)
    if hasattr(context, "stroke"):
        context.stroke()

    red, green, blue = _hex_to_rgb(getattr(widget, "zone_color", "#1D9E75"))
    if hasattr(context, "set_source_rgb"):
        context.set_source_rgb(red, green, blue)
    elif hasattr(context, "set_source_rgba"):
        context.set_source_rgba(red, green, blue, 1.0)
    if hasattr(context, "arc"):
        context.arc(center_x, center_y, radius, start_angle, end_angle)
    if hasattr(context, "stroke"):
        context.stroke()


def _create_gtk_score_ring_widget(gtk_module, score: float, zone_color: str):
    class GtkScoreRingWidget(gtk_module.DrawingArea):  # pragma: no cover - GTK path not available in tests
        def __init__(self, score: float = 0.0, zone_color: str = "#1D9E75") -> None:
            super().__init__()
            self.score = score
            self.zone_color = zone_color
            self.set_draw_func(_draw_score_ring)

        def present(self) -> None:
            return None

        def set_score(self, score: float, zone_color: Optional[str] = None) -> None:
            self.score = score
            if zone_color is not None:
                self.zone_color = zone_color
            self.queue_draw()

    return GtkScoreRingWidget(score=score, zone_color=zone_color)


def create_score_ring_widget(score: float = 0.0, zone_color: str = "#1D9E75"):
    if Gtk is None:
        return ScoreRingWidget(score=score, zone_color=zone_color)
    return _create_gtk_score_ring_widget(Gtk, score, zone_color)


def _hex_to_rgb(color: str) -> tuple:
    text = color.lstrip("#")
    if len(text) != 6:
        return 0.1137, 0.6196, 0.4588
    try:
        red = int(text[0:2], 16) / 255.0
        green = int(text[2:4], 16) / 255.0
        blue = int(text[4:6], 16) / 255.0
    except ValueError:
        return 0.1137, 0.6196, 0.4588
    return red, green, blue
