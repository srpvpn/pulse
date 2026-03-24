"""Evening input helpers for Pulse."""

from datetime import date as date_class
from dataclasses import dataclass
from typing import Callable, List, Sequence

from pulse.i18n import tr
from pulse.ui.theme import apply_classes, build_responsive_page


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


@dataclass(frozen=True)
class EveningPageModel:
    title: str
    subtitle: str
    primary_action: str
    section_titles: tuple
    has_summary_card: bool
    choice_style: str
    sticky_primary_action: bool
    fills_viewport: bool
    large_primary_action: bool
    max_content_width: int
    responsive_layout: bool
    scroll_policy: str


@dataclass(frozen=True)
class CurveEditorLayout:
    minimum_width: int
    height: int


def build_evening_page_model(language: str = "en") -> EveningPageModel:
    return EveningPageModel(
        title=tr(language, "evening.title"),
        subtitle=tr(language, "evening.subtitle"),
        primary_action=tr(language, "evening.save"),
        section_titles=(
            tr(language, "evening.energy_curve"),
            tr(language, "evening.recovery_inputs"),
            tr(language, "evening.context_note"),
        ),
        has_summary_card=False,
        choice_style="compact",
        sticky_primary_action=False,
        fills_viewport=True,
        large_primary_action=True,
        max_content_width=960,
        responsive_layout=True,
        scroll_policy="automatic",
    )


def build_curve_editor_layout() -> CurveEditorLayout:
    return CurveEditorLayout(
        minimum_width=280,
        height=280,
    )


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


def catmull_rom_points(
    points: Sequence[CurvePoint],
    num_segments: int = 20,
) -> List[CurvePoint]:
    ordered_points = _sort_points(points)
    if len(ordered_points) <= 1:
        return ordered_points

    smoothed = [ordered_points[0]]
    for index in range(len(ordered_points) - 1):
        p0 = ordered_points[index - 1] if index > 0 else ordered_points[index]
        p1 = ordered_points[index]
        p2 = ordered_points[index + 1]
        p3 = ordered_points[index + 2] if index + 2 < len(ordered_points) else ordered_points[index + 1]

        for step in range(1, max(1, num_segments)):
            t = step / float(num_segments)
            smoothed.append(_catmull_rom_interpolate(p0, p1, p2, p3, t))
        smoothed.append(CurvePoint(minute_offset=p2.minute_offset, level=_sanitize_level(p2.level)))
    return smoothed


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


def _catmull_rom_interpolate(
    p0: CurvePoint,
    p1: CurvePoint,
    p2: CurvePoint,
    p3: CurvePoint,
    t: float,
) -> CurvePoint:
    t2 = t * t
    t3 = t2 * t
    minute_offset = 0.5 * (
        (2 * p1.minute_offset)
        + (-p0.minute_offset + p2.minute_offset) * t
        + (2 * p0.minute_offset - 5 * p1.minute_offset + 4 * p2.minute_offset - p3.minute_offset) * t2
        + (-p0.minute_offset + 3 * p1.minute_offset - 3 * p2.minute_offset + p3.minute_offset) * t3
    )
    level = 0.5 * (
        (2 * p1.level)
        + (-p0.level + p2.level) * t
        + (2 * p0.level - 5 * p1.level + 4 * p2.level - p3.level) * t2
        + (-p0.level + 3 * p1.level - 3 * p2.level + p3.level) * t3
    )
    return CurvePoint(
        minute_offset=int(round(minute_offset)),
        level=_sanitize_level(level),
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


def create_evening_page(
    on_save: Callable[[str, Sequence[HourlyEnergySample], dict], None],
    language: str = "en",
):
    if Gtk is None:
        return None
    page = build_evening_page_model(language=language)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)

    title = Gtk.Label(label=page.title, xalign=0.0)
    apply_classes(title, "pulse-hero-title")
    subtitle = Gtk.Label(
        label=page.subtitle,
        wrap=True,
        xalign=0.0,
    )
    apply_classes(subtitle, "pulse-subtle")
    content.append(title)
    content.append(subtitle)

    editor = _create_curve_editor()
    editor_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    apply_classes(editor_card, "pulse-card-glass")
    editor_card.set_hexpand(True)
    chart_title = Gtk.Label(label=page.section_titles[0], xalign=0.0)
    apply_classes(chart_title, "heading")
    chart_hint = Gtk.Label(
        label=tr(language, "evening.chart_hint"),
        wrap=True,
        xalign=0.0,
    )
    apply_classes(chart_hint, "pulse-subtle")
    editor_card.append(chart_title)
    editor_card.append(chart_hint)
    editor_card.append(editor)
    content.append(editor_card)

    sleep_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    apply_classes(sleep_row, "pulse-card")
    recovery_title = Gtk.Label(label=page.section_titles[1], xalign=0.0)
    apply_classes(recovery_title, "heading")
    sleep_row.append(recovery_title)
    sleep_row.append(Gtk.Label(label=tr(language, "evening.sleep_hours"), xalign=0.0))
    sleep_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 4.0, 10.0, 0.5)
    sleep_scale.set_value(7.0)
    sleep_scale.set_draw_value(True)
    sleep_row.append(sleep_scale)
    content.append(sleep_row)

    activity_selector = _build_choice_selector(
        tr(language, "evening.activity"),
        (
            tr(language, "option.no"),
            tr(language, "option.some"),
            tr(language, "option.yes"),
        ),
        tr(language, "option.some"),
    )
    stress_selector = _build_choice_selector(
        tr(language, "evening.stress"),
        (
            tr(language, "option.low"),
            tr(language, "option.medium"),
            tr(language, "option.high"),
        ),
        tr(language, "option.medium"),
    )
    content.append(activity_selector["container"])
    content.append(stress_selector["container"])

    note_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    apply_classes(note_card, "pulse-card")
    note_title = Gtk.Label(label=page.section_titles[2], xalign=0.0)
    apply_classes(note_title, "heading")
    note_card.append(note_title)
    note_card.append(Gtk.Label(label=tr(language, "evening.note_prompt"), xalign=0.0))
    note_entry = Gtk.Entry()
    note_entry.set_placeholder_text(tr(language, "evening.note_placeholder"))
    note_card.append(note_entry)
    content.append(note_card)

    save_button = Gtk.Button(label=page.primary_action)
    save_button.add_css_class("suggested-action")
    save_button.set_hexpand(True)
    save_button.set_halign(Gtk.Align.FILL)
    apply_classes(save_button, "pulse-primary-button")

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

    return build_responsive_page(
        content,
        "evening",
        horizontal_policy=Gtk.PolicyType.AUTOMATIC,
        vertical_policy=Gtk.PolicyType.AUTOMATIC,
    )


def _build_choice_selector(title: str, options: Sequence[str], selected: str):
    container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    title_label = Gtk.Label(label=title, xalign=0.0)
    apply_classes(title_label, "pulse-subtle")
    container.append(title_label)
    row = Gtk.FlowBox()
    row.set_selection_mode(Gtk.SelectionMode.NONE)
    row.set_max_children_per_line(3)
    row.set_min_children_per_line(1)
    row.set_column_spacing(6)
    row.set_row_spacing(6)
    buttons = []
    current = {"value": selected}

    def on_clicked(button, value):
        current["value"] = value
        for other in buttons:
            if hasattr(other, "remove_css_class"):
                other.remove_css_class("suggested-action")
            other.set_sensitive(True)
        button.add_css_class("suggested-action")
        button.set_sensitive(False)

    for option in options:
        button = Gtk.Button(label=option)
        apply_classes(button, "pulse-nav-item")
        if option == selected:
            button.add_css_class("suggested-action")
            button.set_sensitive(False)
        button.connect("clicked", on_clicked, option)
        buttons.append(button)
        row.insert(button, -1)
    container.append(row)

    def get_value():
        return current["value"]

    return {"container": container, "get_value": get_value}


def _create_curve_editor():
    class EnergyCurveEditor(Gtk.DrawingArea):
        def __init__(self):
            super().__init__()
            layout = build_curve_editor_layout()
            self.points = [
                CurvePoint(0, 6.0),
                CurvePoint(240, 7.5),
                CurvePoint(540, 4.5),
                CurvePoint(900, 5.0),
            ]
            self.set_hexpand(True)
            self.set_vexpand(False)
            self.set_size_request(layout.minimum_width, layout.height)
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

            smooth_points = catmull_rom_points(points)
            self._draw_fill(context, smooth_points, width, height)
            self._draw_line(context, smooth_points, width, height)

            for point in points:
                red, green, blue = _rgb_for_level(point.level)
                context.set_source_rgb(red, green, blue)
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

        def _draw_line(self, context, points, width, height):
            if len(points) < 2:
                return
            context.set_line_width(2.5)
            for left, right in zip(points, points[1:]):
                red, green, blue = _rgb_for_level((left.level + right.level) / 2.0)
                context.set_source_rgb(red, green, blue)
                context.move_to(
                    self._x_for_offset(left.minute_offset, width),
                    self._y_for_level(left.level, height),
                )
                context.line_to(
                    self._x_for_offset(right.minute_offset, width),
                    self._y_for_level(right.level, height),
                )
                context.stroke()

        def _draw_fill(self, context, points, width, height):
            if len(points) < 2:
                return
            for left, right in zip(points, points[1:]):
                red, green, blue = _rgb_for_level((left.level + right.level) / 2.0)
                context.set_source_rgba(red, green, blue, 0.15)
                context.move_to(self._x_for_offset(left.minute_offset, width), height)
                context.line_to(
                    self._x_for_offset(left.minute_offset, width),
                    self._y_for_level(left.level, height),
                )
                context.line_to(
                    self._x_for_offset(right.minute_offset, width),
                    self._y_for_level(right.level, height),
                )
                context.line_to(self._x_for_offset(right.minute_offset, width), height)
                context.close_path()
                context.fill()

    return EnergyCurveEditor()


def _rgb_for_level(level: float):
    value = _sanitize_level(level)
    if value <= 3.0:
        return (0.8863, 0.2941, 0.2902)
    if value <= 6.0:
        return (0.9373, 0.6235, 0.1529)
    return (0.1137, 0.6196, 0.4588)
