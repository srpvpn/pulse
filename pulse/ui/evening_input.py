"""Evening input helpers for Pulse."""

from datetime import date as date_class
from dataclasses import dataclass
from typing import Callable, List, Sequence


DAY_START_HOUR = 8
DAY_END_HOUR = 23


@dataclass(frozen=True)
class CurvePoint:
    minute_offset: int
    level: float


@dataclass(frozen=True)
class HourlyEnergySample:
    hour: int
    level: float


def sample_energy_curve(
    curve_points: Sequence[CurvePoint],
    start_hour: int = DAY_START_HOUR,
    end_hour: int = DAY_END_HOUR,
) -> List[HourlyEnergySample]:
    points = _sort_points(curve_points)
    if not points:
        return []

    hourly_samples = []
    for hour in range(start_hour, end_hour + 1):
        minute_offset = (hour - start_hour) * 60
        level = _sample_level_at(points, minute_offset)
        hourly_samples.append(HourlyEnergySample(hour=hour, level=level))
    return hourly_samples


def _sort_points(curve_points: Sequence[CurvePoint]) -> List[CurvePoint]:
    points = list(curve_points)
    for index, point in enumerate(points):
        points[index] = CurvePoint(
            minute_offset=int(point.minute_offset),
            level=_sanitize_level(point.level),
        )
    points.sort(key=lambda point: point.minute_offset)
    return points


def _sample_level_at(points: Sequence[CurvePoint], minute_offset: int) -> float:
    if minute_offset <= points[0].minute_offset:
        return points[0].level
    if minute_offset >= points[-1].minute_offset:
        return points[-1].level

    for left, right in zip(points, points[1:]):
        if left.minute_offset <= minute_offset <= right.minute_offset:
            return _interpolate(left, right, minute_offset)

    return points[-1].level


def _interpolate(left: CurvePoint, right: CurvePoint, minute_offset: int) -> float:
    span = right.minute_offset - left.minute_offset
    if span <= 0:
        return right.level
    position = (minute_offset - left.minute_offset) / float(span)
    return left.level + ((right.level - left.level) * position)


def _sanitize_level(level: object) -> float:
    try:
        value = float(level)
    except (TypeError, ValueError):
        value = 1.0
    return max(1.0, min(10.0, value))


def _load_ui():
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # type: ignore

        return Gtk
    except (ImportError, ValueError):
        return None


Gtk = _load_ui()


def create_evening_page(
    on_save: Callable[[str, Sequence[HourlyEnergySample], dict], None],
):
    if Gtk is None:
        return None

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
    content.set_margin_top(24)
    content.set_margin_bottom(24)
    content.set_margin_start(24)
    content.set_margin_end(24)

    title = Gtk.Label(label="Evening Input", xalign=0.0)
    title.add_css_class("title-2")
    subtitle = Gtk.Label(
        label="Draw your day from 08:00 to 23:00, then save sleep, activity, stress, and a short note.",
        wrap=True,
        xalign=0.0,
    )
    subtitle.add_css_class("dim-label")
    content.append(title)
    content.append(subtitle)

    editor = _create_curve_editor()
    editor_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    editor_card.add_css_class("card")
    editor_card.set_margin_start(12)
    editor_card.set_margin_end(12)
    editor_card.append(editor)
    content.append(editor_card)

    sleep_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    sleep_row.add_css_class("card")
    sleep_row.set_margin_start(12)
    sleep_row.set_margin_end(12)
    sleep_row.append(Gtk.Label(label="Sleep hours", xalign=0.0))
    sleep_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 4.0, 10.0, 0.5)
    sleep_scale.set_value(7.0)
    sleep_scale.set_draw_value(True)
    sleep_row.append(sleep_scale)
    content.append(sleep_row)

    activity_selector = _build_choice_selector("Physical activity", ("No", "Some", "Yes"), "Some")
    stress_selector = _build_choice_selector("External stress", ("Low", "Medium", "High"), "Medium")
    content.append(activity_selector["container"])
    content.append(stress_selector["container"])

    note_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    note_card.add_css_class("card")
    note_card.set_margin_start(12)
    note_card.set_margin_end(12)
    note_card.append(Gtk.Label(label="What affected your energy today?", xalign=0.0))
    note_entry = Gtk.Entry()
    note_entry.set_placeholder_text("Optional note")
    note_card.append(note_entry)
    content.append(note_card)

    save_button = Gtk.Button(label="Save today")
    save_button.add_css_class("suggested-action")

    def handle_save(_button):
        samples = sample_energy_curve(editor.points)
        context = {
            "sleep_hours": round(sleep_scale.get_value(), 1),
            "physical_activity": activity_selector["get_value"]().lower(),
            "stress_level": stress_selector["get_value"]().lower(),
            "free_note": note_entry.get_text().strip() or None,
        }
        on_save(date_class.today().isoformat(), samples, context)

    save_button.connect("clicked", handle_save)
    content.append(save_button)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_child(content)
    return scroller


def _build_choice_selector(title: str, options: Sequence[str], selected: str):
    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    container.add_css_class("card")
    container.set_margin_start(12)
    container.set_margin_end(12)
    container.append(Gtk.Label(label=title, xalign=0.0))
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    buttons = []
    current = {"value": selected}

    def on_clicked(button, value):
        current["value"] = value
        for other in buttons:
            other.set_sensitive(other is not button)

    for option in options:
        button = Gtk.Button(label=option)
        if option == selected:
            button.add_css_class("suggested-action")
            button.set_sensitive(False)
        button.connect("clicked", on_clicked, option)
        buttons.append(button)
        row.append(button)
    container.append(row)

    def get_value():
        return current["value"]

    return {"container": container, "get_value": get_value}


def _create_curve_editor():
    class EnergyCurveEditor(Gtk.DrawingArea):
        def __init__(self):
            super().__init__()
            self.points = [
                CurvePoint(0, 6.0),
                CurvePoint(240, 7.5),
                CurvePoint(540, 4.5),
                CurvePoint(900, 5.0),
            ]
            self.set_content_width(860)
            self.set_content_height(280)
            self.set_draw_func(self._draw)
            self._drag_origin_x = 0.0
            self._drag_origin_y = 0.0

            drag = Gtk.GestureDrag()
            drag.connect("drag-begin", self._on_drag_begin)
            drag.connect("drag-update", self._on_drag_update)
            self.add_controller(drag)

        def _on_drag_begin(self, _gesture, start_x, start_y):
            self.points = [self._point_from_coords(start_x, start_y)]
            self._drag_origin_x = start_x
            self._drag_origin_y = start_y
            self.queue_draw()

        def _on_drag_update(self, _gesture, offset_x, offset_y):
            point = self._point_from_coords(self._drag_origin_x + offset_x, self._drag_origin_y + offset_y)
            self.points.append(point)
            self.points = _sort_points(self.points)
            self.queue_draw()

        def _point_from_coords(self, x, y):
            width = max(self.get_width(), 1)
            height = max(self.get_height(), 1)
            x_ratio = max(0.0, min(x / float(width), 1.0))
            y_ratio = max(0.0, min(y / float(height), 1.0))
            minute_offset = int(round(x_ratio * ((DAY_END_HOUR - DAY_START_HOUR) * 60)))
            level = 10.0 - (y_ratio * 9.0)
            return CurvePoint(minute_offset=minute_offset, level=_sanitize_level(level))

        def _draw(self, _widget, context, width, height):
            context.set_source_rgba(0.2, 0.2, 0.2, 0.08)
            for hour in range(DAY_START_HOUR, DAY_END_HOUR + 1):
                x = ((hour - DAY_START_HOUR) / float(DAY_END_HOUR - DAY_START_HOUR)) * width
                context.move_to(x, 0)
                context.line_to(x, height)
            context.stroke()

            points = _sort_points(self.points)
            if not points:
                return

            context.set_line_width(3.0)
            context.set_source_rgb(0.1137, 0.6196, 0.4588)
            first = points[0]
            context.move_to(self._x_for_offset(first.minute_offset, width), self._y_for_level(first.level, height))
            for point in points[1:]:
                context.line_to(self._x_for_offset(point.minute_offset, width), self._y_for_level(point.level, height))
            context.stroke()

            for point in points:
                context.set_source_rgb(0.1137, 0.6196, 0.4588)
                context.arc(
                    self._x_for_offset(point.minute_offset, width),
                    self._y_for_level(point.level, height),
                    3.5,
                    0.0,
                    6.283,
                )
                context.fill()

        def _x_for_offset(self, minute_offset, width):
            return (minute_offset / float((DAY_END_HOUR - DAY_START_HOUR) * 60)) * width

        def _y_for_level(self, level, height):
            return ((10.0 - _sanitize_level(level)) / 9.0) * height

    return EnergyCurveEditor()
