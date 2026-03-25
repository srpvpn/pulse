"""Main window for Pulse."""

from datetime import date as date_class, timedelta
from statistics import mean
from typing import Optional

from pulse.advice_engine import AdviceContext, select_advice
from pulse.burnout_engine import BurnoutEntry, BurnoutScoreResult, compute_burnout_score
from pulse.pattern_engine import (
    DailyEnergyPoint,
    IntradayEnergySample,
    WeeklyInsightDay,
    count_consecutive_low_energy_days,
    detect_energy_trend,
    estimate_ultradian_cycles,
    generate_weekly_insights,
)
from pulse.i18n import tr
from pulse.ui.dashboard import DashboardViewModel, build_dashboard_view_model, create_dashboard_page
from pulse.ui.evening_input import create_evening_page
from pulse.ui.onboarding import create_onboarding_page
from pulse.ui.patterns import PatternCorrelation, build_patterns_view_model, create_patterns_page
from pulse.ui.rituals import Ritual, create_rituals_page
from pulse.ui.settings import create_settings_page
from pulse.ui.theme import THEME, apply_classes, apply_theme_mode, install_theme
from pulse.ui.weekly_review import (
    MBICheckin,
    build_weekly_review_view_model,
    compute_mbi_correction,
    create_weekly_review_page,
)


def _load_adw():
    try:
        import gi

        gi.require_version("Adw", "1")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Adw, Gtk  # type: ignore

        if hasattr(Gtk, "init_check") and not Gtk.init_check():
            return None, None
        return Adw, Gtk
    except (ImportError, ValueError):
        return None, None


Adw, Gtk = _load_adw()


SIDEBAR_COLLAPSE_WIDTH = 1080


def _layout_mode_for_width(width: int) -> str:
    return "narrow" if width and width < SIDEBAR_COLLAPSE_WIDTH else "wide"


if Adw is None or Gtk is None:
    class _FallbackWindow(object):
        def __init__(self, application: Optional[object] = None, **kwargs) -> None:
            self.application = application
            self.kwargs = kwargs
            self.title = "Pulse"
            self.uses_header_bar_top_chrome = False

        def present(self) -> None:
            return None

    WindowBase = _FallbackWindow
else:
    WindowBase = Adw.ApplicationWindow


class PulseMainWindow(WindowBase):
    """Primary application window."""

    def __init__(self, application: Optional[object] = None, initial_state: Optional[object] = None) -> None:
        super(PulseMainWindow, self).__init__(application=application)
        self.application = application
        self.initial_state = initial_state
        self.uses_compact_stack_sizing = True
        self.uses_fixed_sidebar_width = True
        self.supports_narrow_layout = True
        self.uses_overlay_split_view = True
        self.uses_window_breakpoints = True
        self.uses_header_bar_top_chrome = True
        self.current_view = getattr(initial_state, "current_view", "onboarding")
        self.reminder_time = getattr(initial_state, "reminder_time", "20:00")
        self.language = getattr(initial_state, "language", "en")
        self.theme_mode = getattr(initial_state, "theme_mode", "system")
        self.patterns_range = "30D"
        self.nav_items = (
            ("dashboard", "nav.dashboard"),
            ("evening", "nav.evening"),
            ("patterns", "nav.patterns"),
            ("review", "nav.review"),
            ("rituals", "nav.rituals"),
            ("settings", "nav.settings"),
        )
        self._nav_buttons = {}
        if Gtk is not None and Adw is not None:
            install_theme(theme_mode=self.theme_mode)
            apply_theme_mode(self.theme_mode)
            self.set_title("Pulse")
            self.set_default_size(1220, 820)
            self._layout_mode = "wide"
            self._split_view = None
            self._compact_header = None
            self._window_header_bar = None
            self._shell_breakpoint = None
            self._toast_overlay = Adw.ToastOverlay()
            self.set_content(self._toast_overlay)
            self.connect("notify::width", self._on_width_changed)
            self._rebuild_content()

    def set_state(self, state: Optional[object]) -> None:
        self.initial_state = state
        self.current_view = getattr(state, "current_view", self.current_view)
        self.reminder_time = getattr(state, "reminder_time", self.reminder_time)
        self.language = getattr(state, "language", self.language)
        self.theme_mode = getattr(state, "theme_mode", self.theme_mode)
        if Gtk is not None and Adw is not None:
            install_theme(theme_mode=self.theme_mode)
            apply_theme_mode(self.theme_mode)
            self._rebuild_content()

    def _rebuild_content(self) -> None:
        if self.current_view == "onboarding":
            child = create_onboarding_page(self.reminder_time, self._handle_onboarding_complete, language=self.language)
        else:
            child = self._build_shell()
        self._toast_overlay.set_child(self._wrap_with_window_chrome(child))

    def _handle_onboarding_complete(self, reminder_time: str) -> None:
        if self.application is not None and hasattr(self.application, "complete_onboarding"):
            state = self.application.complete_onboarding(reminder_time)
            self.set_state(state)
            self._show_toast(tr(self.language, "toast.reminder_saved"))

    def _handle_evening_save(self, entry_date: str, samples, context: dict) -> None:
        if self.application is None:
            return
        self.application.database.save_evening_input(
            date=entry_date,
            hourly_samples=samples,
            sleep_hours=context.get("sleep_hours"),
            physical_activity=context.get("physical_activity"),
            stress_level=context.get("stress_level"),
            free_note=context.get("free_note"),
        )
        self.current_view = "dashboard"
        self._rebuild_content()
        self._show_toast(tr(self.language, "toast.day_saved"))

    def _show_toast(self, message: str) -> None:
        if Adw is None or not hasattr(self, "_toast_overlay"):
            return
        try:
            toast = Adw.Toast.new(message)
            self._toast_overlay.add_toast(toast)
        except Exception:
            return

    def _build_shell(self):
        self._nav_buttons = {}
        if hasattr(Adw, "OverlaySplitView"):
            return self._build_overlay_split_shell()

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        apply_classes(root, "pulse-root")

        sidebar = self._build_sidebar()
        root.append(sidebar)

        canvas = Gtk.Overlay()
        apply_classes(canvas, "pulse-canvas")
        canvas.set_hexpand(True)
        canvas.set_vexpand(True)

        self._stack = self._build_stack()
        canvas.set_child(self._stack)

        root.append(canvas)
        self._set_visible_view(self.current_view if self.current_view != "onboarding" else "dashboard")
        return root

    def _wrap_with_window_chrome(self, child):
        if Adw is None or child is None:
            return child
        if not hasattr(Adw, "ToolbarView"):
            return child
        toolbar_view = Adw.ToolbarView()
        header_bar = self._build_window_header_bar()
        toolbar_view.add_top_bar(header_bar)
        toolbar_view.set_content(child)
        return toolbar_view

    def _build_overlay_split_shell(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        apply_classes(root, "pulse-root")

        self._compact_header = self._build_compact_header()
        root.append(self._compact_header)

        self._split_view = Adw.OverlaySplitView()
        if hasattr(self._split_view, "set_max_sidebar_width"):
            self._split_view.set_max_sidebar_width(240)
        if hasattr(self._split_view, "set_min_sidebar_width"):
            self._split_view.set_min_sidebar_width(220)
        if hasattr(self._split_view, "set_sidebar_width_fraction"):
            self._split_view.set_sidebar_width_fraction(0.2)
        if hasattr(self._split_view, "set_enable_show_gesture"):
            self._split_view.set_enable_show_gesture(True)
        if hasattr(self._split_view, "set_enable_hide_gesture"):
            self._split_view.set_enable_hide_gesture(True)

        self._split_view.set_sidebar(self._build_sidebar())
        self._split_view.set_content(self._build_content_canvas())
        self._install_window_breakpoints()
        root.append(self._split_view)
        self._sync_split_view_layout(force_hide=True)
        self._set_visible_view(self.current_view if self.current_view != "onboarding" else "dashboard")
        return root

    def _build_content_canvas(self):
        canvas = Gtk.Overlay()
        apply_classes(canvas, "pulse-canvas")
        canvas.set_hexpand(True)
        canvas.set_vexpand(True)
        self._stack = self._build_stack()
        canvas.set_child(self._stack)
        return canvas

    def _build_stack(self):
        stack = Adw.ViewStack()
        if hasattr(stack, "set_vhomogeneous"):
            stack.set_vhomogeneous(False)
        if hasattr(stack, "set_hhomogeneous"):
            stack.set_hhomogeneous(False)
        stack.set_vexpand(True)
        stack.set_hexpand(True)
        stack.add_titled(self._build_dashboard_page(), "dashboard", tr(self.language, "nav.dashboard"))
        stack.add_titled(create_evening_page(self._handle_evening_save, self.language), "evening", tr(self.language, "nav.evening"))
        stack.add_titled(self._build_patterns_page(), "patterns", tr(self.language, "nav.patterns"))
        stack.add_titled(self._build_review_page(), "review", tr(self.language, "nav.review"))
        stack.add_titled(self._build_rituals_page(), "rituals", tr(self.language, "nav.rituals"))
        stack.add_titled(self._build_settings_page(), "settings", tr(self.language, "nav.settings"))
        return stack

    def _build_compact_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(12)
        header.set_margin_bottom(8)
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_hexpand(True)
        apply_classes(header, "pulse-mobile-header")

        toggle = Gtk.Button()
        if hasattr(toggle, "set_icon_name"):
            toggle.set_icon_name("sidebar-show-symbolic")
        else:
            toggle.set_label("Menu")
        if hasattr(toggle, "set_tooltip_text"):
            toggle.set_tooltip_text("Show navigation")
        toggle.connect("clicked", self._on_sidebar_toggle_clicked)
        apply_classes(toggle, "pulse-mobile-toggle")

        title_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_group.set_hexpand(True)
        brand = Gtk.Label(label=tr(self.language, "app.name"), xalign=0.0)
        apply_classes(brand, "pulse-brand")
        reminder = Gtk.Label(label=tr(self.language, "sidebar.reminder", time=self.reminder_time), xalign=0.0)
        apply_classes(reminder, "pulse-subtle")
        title_group.append(brand)
        title_group.append(reminder)

        header.append(toggle)
        header.append(title_group)
        return header

    def _build_window_header_bar(self):
        if Adw is None:
            return None
        header_bar = Adw.HeaderBar()
        if hasattr(header_bar, "set_show_title"):
            header_bar.set_show_title(True)
        if hasattr(header_bar, "set_show_start_title_buttons"):
            header_bar.set_show_start_title_buttons(True)
        if hasattr(header_bar, "set_show_end_title_buttons"):
            header_bar.set_show_end_title_buttons(True)
        return header_bar

    def _build_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sidebar.set_hexpand(False)
        sidebar.set_halign(Gtk.Align.START)
        if hasattr(sidebar, "set_width_request"):
            sidebar.set_width_request(THEME.sidebar_width)
        sidebar.set_size_request(THEME.sidebar_width, -1)
        apply_classes(sidebar, "pulse-sidebar")

        logo_block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        brand = Gtk.Label(label=tr(self.language, "app.name"), xalign=0.0)
        apply_classes(brand, "pulse-brand")
        subtitle = Gtk.Label(label=tr(self.language, "app.subtitle"), xalign=0.0, wrap=True)
        apply_classes(subtitle, "pulse-subtle")
        logo_block.append(brand)
        logo_block.append(subtitle)
        sidebar.append(logo_block)

        reminder = Gtk.Label(label=tr(self.language, "sidebar.reminder", time=self.reminder_time), xalign=0.0)
        apply_classes(reminder, "pulse-chip")
        sidebar.append(reminder)

        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for view_name, label_key in self.nav_items:
            button = Gtk.Button(label=tr(self.language, label_key))
            button.set_halign(Gtk.Align.FILL)
            button.set_hexpand(True)
            button.connect("clicked", self._on_nav_clicked, view_name)
            apply_classes(button, "pulse-nav-item")
            self._nav_buttons[view_name] = button
            nav.append(button)
        sidebar.append(nav)

        sidebar.append(Gtk.Box(vexpand=True))
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_hexpand(False)
        scroller.set_vexpand(True)
        scroller.set_child(sidebar)
        return scroller

    def _on_nav_clicked(self, _button, view_name: str) -> None:
        self.current_view = view_name
        self._set_visible_view(view_name)
        if self._is_split_view_collapsed() and hasattr(self._split_view, "set_show_sidebar"):
            self._split_view.set_show_sidebar(False)

    def _set_visible_view(self, view_name: str) -> None:
        if hasattr(self, "_stack"):
            visible_view = view_name if view_name in {item[0] for item in self.nav_items} else "dashboard"
            self._stack.set_visible_child_name(visible_view)
            self.current_view = visible_view
        self._sync_nav_state()

    def _sync_nav_state(self) -> None:
        for view_name, button in self._nav_buttons.items():
            if hasattr(button, "remove_css_class"):
                button.remove_css_class("pulse-nav-item-active")
            if view_name == self.current_view:
                apply_classes(button, "pulse-nav-item-active")

    def _current_width(self) -> int:
        if Gtk is None:
            return 1220
        try:
            width = self.get_width()
        except Exception:
            width = 0
        return width or 1220

    def _on_width_changed(self, *_args) -> None:
        if self.current_view == "onboarding":
            return
        if self._shell_breakpoint is not None:
            return
        new_mode = _layout_mode_for_width(self._current_width())
        if self._split_view is not None:
            if getattr(self, "_layout_mode", None) != new_mode:
                self._layout_mode = new_mode
                self._sync_split_view_layout(force_hide=new_mode == "narrow")
            else:
                self._sync_split_view_layout(force_hide=False)
            return
        if getattr(self, "_layout_mode", None) == new_mode:
            return
        self._layout_mode = new_mode
        self._rebuild_content()

    def _sync_split_view_layout(self, force_hide: bool) -> None:
        if self._split_view is None:
            return
        narrow = _layout_mode_for_width(self._current_width()) == "narrow"
        if hasattr(self._split_view, "set_collapsed"):
            self._split_view.set_collapsed(narrow)
        if self._compact_header is not None:
            self._compact_header.set_visible(narrow)
        if hasattr(self._split_view, "set_show_sidebar"):
            if narrow:
                if force_hide:
                    self._split_view.set_show_sidebar(False)
            else:
                self._split_view.set_show_sidebar(True)

    def _is_split_view_collapsed(self) -> bool:
        if self._split_view is None:
            return False
        if hasattr(self._split_view, "get_collapsed"):
            try:
                return bool(self._split_view.get_collapsed())
            except Exception:
                return False
        return False

    def _on_sidebar_toggle_clicked(self, _button) -> None:
        if self._split_view is None or not hasattr(self._split_view, "set_show_sidebar"):
            return
        is_shown = False
        if hasattr(self._split_view, "get_show_sidebar"):
            try:
                is_shown = bool(self._split_view.get_show_sidebar())
            except Exception:
                is_shown = False
        self._split_view.set_show_sidebar(not is_shown)

    def _install_window_breakpoints(self) -> None:
        if self._split_view is None or self._compact_header is None:
            return
        if not hasattr(self, "add_breakpoint") or not hasattr(Adw, "Breakpoint"):
            return

        self._split_view.set_collapsed(False)
        self._split_view.set_show_sidebar(True)
        self._compact_header.set_visible(False)

        condition = Adw.BreakpointCondition.parse("max-width: {width}px".format(width=SIDEBAR_COLLAPSE_WIDTH))
        if condition is None:
            return
        breakpoint = Adw.Breakpoint.new(condition)
        breakpoint.add_setter(self._split_view, "collapsed", True)
        breakpoint.add_setter(self._split_view, "show-sidebar", False)
        breakpoint.add_setter(self._compact_header, "visible", True)
        self.add_breakpoint(breakpoint)
        self._shell_breakpoint = breakpoint

    def _build_dashboard_page(self):
        daily_points = self._load_daily_points(limit=30)
        entries = self._load_burnout_entries(limit=14)
        has_data = bool(entries)
        if entries:
            latest_mbi = self._latest_mbi_correction()
            burnout = compute_burnout_score(entries, mbi_correction=latest_mbi)
            advice = select_advice(
                AdviceContext(
                    burnout_score=burnout.score,
                    trend=detect_energy_trend(daily_points),
                    consecutive_low_days=count_consecutive_low_energy_days(daily_points),
                    last_sleep=entries[-1].sleep_hours,
                    sleep_correlation=self._sleep_correlation(entries),
                )
            )
            ultradian_cycles = estimate_ultradian_cycles(self._latest_intraday_samples())
            view_model = build_dashboard_view_model(burnout, advice, ultradian_cycles=ultradian_cycles, language=self.language)
        else:
            empty_state = build_dashboard_view_model(
                BurnoutScoreResult(score=50.0, ali=0.0, rqs=50.0, trend_penalty=0.0, mbi_correction=0.0),
                None,
                ultradian_cycles=0,
                language=self.language,
            )
            view_model = DashboardViewModel(
                score=empty_state.score,
                score_zone=empty_state.score_zone,
                primary_message=tr(self.language, "dashboard.no_baseline"),
                primary_action=tr(self.language, "dashboard.open_evening"),
                primary_science_ref=tr(self.language, "dashboard.predictive_note"),
                ultradian_cycles=empty_state.ultradian_cycles,
                score_label=empty_state.score_label,
                zone_pill=empty_state.zone_pill,
                secondary_metrics=empty_state.secondary_metrics,
                headline=empty_state.headline,
                score_card_title=empty_state.score_card_title,
                insight_title=empty_state.insight_title,
                reference_cards=empty_state.reference_cards,
            )
        return create_dashboard_page(view_model, has_data=has_data)

    def _build_patterns_page(self):
        points = self._load_daily_points_for_range(self.patterns_range)
        correlations = self._build_correlation_cards(self.patterns_range)
        trajectory_scores = self._rolling_burnout_scores(self.patterns_range)
        view_model = build_patterns_view_model(
            points,
            correlations,
            trajectory_scores,
            selected_range=self.patterns_range,
            language=self.language,
        )
        return create_patterns_page(view_model, on_select_range=self._handle_patterns_range_change, language=self.language)

    def _build_review_page(self):
        week_start, week_end = _current_week_range()
        week_days = self._load_weekly_insight_days(week_start, week_end)
        historical_days = self._load_historical_weekly_insight_days(before_date=week_start)
        this_week = _average_day_energy(week_days)
        previous_week = _average_energy(self._load_daily_points_between(*_previous_week_range(week_start)))
        mbi_checkin = self._latest_mbi_checkin()
        weekly_note = self.application.database.weekly_note_for_week(week_start) if self.application is not None else ""
        week_index = date_class.today().isocalendar()[1]
        view_model = build_weekly_review_view_model(
            week_start=week_start,
            week_end=week_end,
            this_week_average_energy=this_week,
            previous_week_average_energy=previous_week,
            insights=generate_weekly_insights(week_days, historical_days, language=self.language),
            week_index=week_index,
            language=self.language,
        )
        return create_weekly_review_page(
            view_model,
            on_save=self._handle_weekly_review_save,
            initial_checkin=mbi_checkin,
            initial_note=weekly_note or "",
            language=self.language,
        )

    def _build_rituals_page(self):
        rituals = self.application.load_all_rituals() if self.application is not None else []
        return create_rituals_page(rituals, on_save=self._handle_ritual_save, language=self.language)

    def _build_settings_page(self):
        return create_settings_page(
            self.language,
            self.theme_mode,
            self._handle_language_change,
            self._handle_theme_mode_change,
        )

    def _handle_weekly_review_save(self, checkin: MBICheckin, note: str) -> None:
        if self.application is None:
            return
        week_start, _week_end = _current_week_range()
        self.application.database.save_weekly_checkin(
            week=week_start,
            exhaustion=checkin.exhaustion,
            cynicism=checkin.cynicism,
            efficacy=checkin.efficacy,
            note=note,
        )
        self._rebuild_content()
        self._show_toast(tr(self.language, "toast.review_saved"))

    def _handle_patterns_range_change(self, range_key: str) -> None:
        self.patterns_range = range_key
        self.current_view = "patterns"
        self._rebuild_content()

    def _handle_ritual_save(self, ritual: Ritual) -> None:
        if self.application is None:
            return
        self.application.database.save_ritual(
            ritual_id=ritual.ritual_id,
            label=ritual.label,
            time=ritual.time,
            active=ritual.active,
        )
        self._rebuild_content()
        self._show_toast(tr(self.language, "toast.ritual_saved"))

    def _handle_language_change(self, language: str) -> None:
        if self.application is None:
            return
        state = self.application.set_language(language)
        self.set_state(state)
        self.current_view = "settings"
        self._rebuild_content()
        self._show_toast(tr(self.language, "settings.saved"))

    def _handle_theme_mode_change(self, theme_mode: str) -> None:
        if self.application is None or not hasattr(self.application, "set_theme_mode"):
            return
        state = self.application.set_theme_mode(theme_mode)
        self.set_state(state)
        self.current_view = "settings"
        self._rebuild_content()
        self._show_toast(tr(self.language, "settings.saved"))

    def _build_rituals_popover(self):
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        rituals = self.application.load_rituals() if self.application is not None else []
        if rituals:
            for ritual in rituals:
                label = Gtk.Label(
                    label="{time} · {label}".format(time=ritual.time, label=ritual.label),
                    xalign=0.0,
                )
                box.append(label)
        else:
            empty = Gtk.Label(label="No rituals configured yet.", xalign=0.0)
            empty.add_css_class("dim-label")
            box.append(empty)
        popover.set_child(box)
        return popover

    def _load_daily_points(self, limit: int = 30):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT date, AVG(level) AS average_energy
                FROM energy_logs
                GROUP BY date
                ORDER BY date
                """
            ).fetchall()
        rows = rows[-limit:]
        return [DailyEnergyPoint(date=row["date"], average_energy=float(row["average_energy"])) for row in rows]

    def _load_daily_points_for_range(self, range_key: str):
        if self.application is None:
            return []
        start_date = _range_start_date(range_key)
        with self.application.database.connect() as connection:
            if start_date is None:
                rows = connection.execute(
                    """
                    SELECT date, AVG(level) AS average_energy
                    FROM energy_logs
                    GROUP BY date
                    ORDER BY date
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT date, AVG(level) AS average_energy
                    FROM energy_logs
                    WHERE date >= ?
                    GROUP BY date
                    ORDER BY date
                    """,
                    (start_date,),
                ).fetchall()
        return [DailyEnergyPoint(date=row["date"], average_energy=float(row["average_energy"])) for row in rows]

    def _load_burnout_entries(self, limit: int = 14):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT e.date AS date,
                       AVG(e.level) AS average_energy,
                       c.sleep_hours AS sleep_hours,
                       c.stress_level AS stress_level,
                       c.physical_activity AS physical_activity
                FROM energy_logs e
                LEFT JOIN daily_context c ON c.date = e.date
                GROUP BY e.date
                ORDER BY e.date
                """
            ).fetchall()
        rows = rows[-limit:]
        return [
            BurnoutEntry(
                date=row["date"],
                average_energy=float(row["average_energy"]),
                sleep_hours=row["sleep_hours"],
                stress_level=row["stress_level"],
                physical_activity=row["physical_activity"],
            )
            for row in rows
        ]

    def _latest_intraday_samples(self):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            latest = connection.execute("SELECT MAX(date) AS latest_date FROM energy_logs").fetchone()
            if latest is None or latest["latest_date"] is None:
                return []
            rows = connection.execute(
                """
                SELECT hour, level
                FROM energy_logs
                WHERE date = ?
                ORDER BY hour
                """,
                (latest["latest_date"],),
            ).fetchall()
        return [
            IntradayEnergySample(
                minute_offset=(int(row["hour"]) - 8) * 60,
                energy=float(row["level"]),
                duration_minutes=60,
            )
            for row in rows
        ]

    def _rolling_burnout_scores(self, range_key: str = "30D"):
        entries = self._load_burnout_entries_for_range(range_key)
        if len(entries) < 2:
            return []
        latest_mbi = self._latest_mbi_correction()
        scores = []
        for index in range(2, len(entries) + 1):
            scores.append(compute_burnout_score(entries[:index], mbi_correction=latest_mbi))
        return scores

    def _build_correlation_cards(self, range_key: str = "30D"):
        if self.application is None:
            return []
        start_date = _range_start_date(range_key)
        with self.application.database.connect() as connection:
            if start_date is None:
                rows = connection.execute(
                    """
                    SELECT e.date AS date,
                           AVG(e.level) AS average_energy,
                           c.sleep_hours AS sleep_hours,
                           c.physical_activity AS physical_activity,
                           c.stress_level AS stress_level
                    FROM energy_logs e
                    LEFT JOIN daily_context c ON c.date = e.date
                    GROUP BY e.date
                    ORDER BY e.date
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT e.date AS date,
                           AVG(e.level) AS average_energy,
                           c.sleep_hours AS sleep_hours,
                           c.physical_activity AS physical_activity,
                           c.stress_level AS stress_level
                    FROM energy_logs e
                    LEFT JOIN daily_context c ON c.date = e.date
                    WHERE e.date >= ?
                    GROUP BY e.date
                    ORDER BY e.date
                    """,
                    (start_date,),
                ).fetchall()

        data = [
            {
                "date": row["date"],
                "average_energy": float(row["average_energy"]),
                "sleep_hours": row["sleep_hours"],
                "physical_activity": (row["physical_activity"] or "").lower(),
                "stress_level": (row["stress_level"] or "").lower(),
            }
            for row in rows
        ]
        cards = []

        sleep_high = [row["average_energy"] for row in data if row["sleep_hours"] is not None and row["sleep_hours"] >= 7.0]
        sleep_low = [row["average_energy"] for row in data if row["sleep_hours"] is not None and row["sleep_hours"] < 7.0]
        if sleep_high and sleep_low:
            cards.append(
                PatternCorrelation(
                    label=tr(self.language, "patterns.correlation.sleep.label"),
                    delta=mean(sleep_high) - mean(sleep_low),
                    condition=tr(self.language, "patterns.correlation.sleep.condition"),
                    science_ref="Sleep and cognitive performance (Walker, 2017)",
                )
            )

        active = [row["average_energy"] for row in data if row["physical_activity"] in ("yes", "some")]
        inactive = [row["average_energy"] for row in data if row["physical_activity"] in ("no", "none", "")]
        if active and inactive:
            cards.append(
                PatternCorrelation(
                    label=tr(self.language, "patterns.correlation.activity.label"),
                    delta=mean(active) - mean(inactive),
                    condition=tr(self.language, "patterns.correlation.activity.condition"),
                    science_ref="Recovery cycles (Sonnentag)",
                )
            )

        low_stress = [row["average_energy"] for row in data if row["stress_level"] == "low"]
        high_stress = [row["average_energy"] for row in data if row["stress_level"] == "high"]
        if low_stress and high_stress:
            cards.append(
                PatternCorrelation(
                    label=tr(self.language, "patterns.correlation.stress.label"),
                    delta=mean(low_stress) - mean(high_stress),
                    condition=tr(self.language, "patterns.correlation.stress.condition"),
                    science_ref="Psychological detachment (Sonnentag, 2003)",
                )
            )
        return cards

    def _load_burnout_entries_for_range(self, range_key: str):
        if self.application is None:
            return []
        start_date = _range_start_date(range_key)
        with self.application.database.connect() as connection:
            if start_date is None:
                rows = connection.execute(
                    """
                    SELECT e.date AS date,
                           AVG(e.level) AS average_energy,
                           c.sleep_hours AS sleep_hours,
                           c.stress_level AS stress_level,
                           c.physical_activity AS physical_activity
                    FROM energy_logs e
                    LEFT JOIN daily_context c ON c.date = e.date
                    GROUP BY e.date
                    ORDER BY e.date
                    """
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT e.date AS date,
                           AVG(e.level) AS average_energy,
                           c.sleep_hours AS sleep_hours,
                           c.stress_level AS stress_level,
                           c.physical_activity AS physical_activity
                    FROM energy_logs e
                    LEFT JOIN daily_context c ON c.date = e.date
                    WHERE e.date >= ?
                    GROUP BY e.date
                    ORDER BY e.date
                    """,
                    (start_date,),
                ).fetchall()
        return [
            BurnoutEntry(
                date=row["date"],
                average_energy=float(row["average_energy"]),
                sleep_hours=row["sleep_hours"],
                stress_level=row["stress_level"],
                physical_activity=row["physical_activity"],
            )
            for row in rows
        ]

    def _latest_mbi_correction(self):
        mbi = self._latest_mbi_checkin()
        if mbi is None:
            return 0.0
        return compute_mbi_correction(mbi)

    def _latest_mbi_checkin(self):
        if self.application is None:
            return None
        row = self.application.database.latest_mbi_checkin()
        if row is None:
            return None
        return MBICheckin(
            exhaustion=int(row["exhaustion"]),
            cynicism=int(row["cynicism"]),
            efficacy=int(row["efficacy"]),
        )

    def _sleep_correlation(self, entries):
        pairs = [(entry.sleep_hours, entry.average_energy) for entry in entries if entry.sleep_hours is not None]
        if len(pairs) < 3:
            return None
        sleeps = [pair[0] for pair in pairs]
        energies = [pair[1] for pair in pairs]
        sleep_mean = mean(sleeps)
        energy_mean = mean(energies)
        numerator = sum((sleep - sleep_mean) * (energy - energy_mean) for sleep, energy in pairs)
        sleep_variance = sum((sleep - sleep_mean) ** 2 for sleep in sleeps)
        energy_variance = sum((energy - energy_mean) ** 2 for energy in energies)
        if sleep_variance <= 0 or energy_variance <= 0:
            return None
        return numerator / ((sleep_variance ** 0.5) * (energy_variance ** 0.5))

    def _load_daily_points_between(self, start_date: str, end_date: str):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT date, AVG(level) AS average_energy
                FROM energy_logs
                WHERE date BETWEEN ? AND ?
                GROUP BY date
                ORDER BY date
                """,
                (start_date, end_date),
            ).fetchall()
        return [DailyEnergyPoint(date=row["date"], average_energy=float(row["average_energy"])) for row in rows]

    def _load_weekly_insight_days(self, start_date: str, end_date: str):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT e.date AS date,
                       AVG(e.level) AS average_energy,
                       c.sleep_hours AS sleep_hours,
                       c.physical_activity AS physical_activity
                FROM energy_logs e
                LEFT JOIN daily_context c ON c.date = e.date
                WHERE e.date BETWEEN ? AND ?
                GROUP BY e.date
                ORDER BY e.date
                """,
                (start_date, end_date),
            ).fetchall()
        return [
            WeeklyInsightDay(
                date=row["date"],
                avg_energy=float(row["average_energy"]),
                sleep_hours=row["sleep_hours"],
                physical_activity=row["physical_activity"],
            )
            for row in rows
        ]

    def _load_historical_weekly_insight_days(self, before_date: str):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT e.date AS date,
                       AVG(e.level) AS average_energy,
                       c.sleep_hours AS sleep_hours,
                       c.physical_activity AS physical_activity
                FROM energy_logs e
                LEFT JOIN daily_context c ON c.date = e.date
                WHERE e.date < ?
                GROUP BY e.date
                ORDER BY e.date
                """,
                (before_date,),
            ).fetchall()
        return [
            WeeklyInsightDay(
                date=row["date"],
                avg_energy=float(row["average_energy"]),
                sleep_hours=row["sleep_hours"],
                physical_activity=row["physical_activity"],
            )
            for row in rows
        ]


def _average_energy(points):
    if not points:
        return 0.0
    return mean(point.average_energy for point in points)


def _average_day_energy(days):
    if not days:
        return 0.0
    return mean(day.avg_energy for day in days)


def _current_week_range(today=None):
    current = today or date_class.today()
    week_start = current - timedelta(days=current.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start.isoformat(), week_end.isoformat()


def _previous_week_range(week_start_text: str):
    week_start = date_class.fromisoformat(week_start_text)
    previous_start = week_start - timedelta(days=7)
    previous_end = previous_start + timedelta(days=6)
    return previous_start.isoformat(), previous_end.isoformat()


def _range_start_date(range_key: str):
    today = date_class.today()
    if range_key == "7D":
        return (today - timedelta(days=6)).isoformat()
    if range_key == "30D":
        return (today - timedelta(days=29)).isoformat()
    if range_key == "90D":
        return (today - timedelta(days=89)).isoformat()
    if range_key == "1Y":
        return (today - timedelta(days=364)).isoformat()
    return None
