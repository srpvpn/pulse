"""Main window for Pulse."""

from datetime import date as date_class, timedelta
from statistics import mean
from typing import Optional

from pulse.advice_engine import AdviceContext, select_advice
from pulse.burnout_engine import BurnoutEntry, BurnoutScoreResult, compute_burnout_score
from pulse.pattern_engine import (
    DailyEnergyPoint,
    IntradayEnergySample,
    count_consecutive_low_energy_days,
    detect_energy_trend,
    estimate_ultradian_cycles,
)
from pulse.ui.dashboard import DashboardViewModel, build_dashboard_view_model, create_dashboard_page
from pulse.ui.evening_input import create_evening_page
from pulse.ui.onboarding import create_onboarding_page
from pulse.ui.patterns import PatternCorrelation, build_patterns_view_model, create_patterns_page
from pulse.ui.rituals import Ritual
from pulse.ui.weekly_review import MBICheckin, build_weekly_review_view_model, create_weekly_review_page


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


if Adw is None or Gtk is None:
    class _FallbackWindow(object):
        def __init__(self, application: Optional[object] = None, **kwargs) -> None:
            self.application = application
            self.kwargs = kwargs
            self.title = "Pulse"

        def present(self) -> None:
            return None

    WindowBase = _FallbackWindow
else:
    WindowBase = Adw.ApplicationWindow


class PulseMainWindow(WindowBase):
    """Primary application window."""

    def __init__(self, application: Optional[object] = None, initial_state: Optional[object] = None) -> None:
        super(PulseMainWindow, self).__init__(application=application)
        self.initial_state = initial_state
        self.current_view = getattr(initial_state, "current_view", "onboarding")
        self.reminder_time = getattr(initial_state, "reminder_time", "20:00")
        if Gtk is not None and Adw is not None:
            self.set_title("Pulse")
            self.set_default_size(980, 760)
            self._toast_overlay = Adw.ToastOverlay()
            self.set_content(self._toast_overlay)
            self._rebuild_content()

    def set_state(self, state: Optional[object]) -> None:
        self.initial_state = state
        self.current_view = getattr(state, "current_view", self.current_view)
        self.reminder_time = getattr(state, "reminder_time", self.reminder_time)
        if Gtk is not None and Adw is not None:
            self._rebuild_content()

    def _rebuild_content(self) -> None:
        if self.current_view == "onboarding":
            child = create_onboarding_page(self.reminder_time, self._handle_onboarding_complete)
        else:
            child = self._build_shell()
        self._toast_overlay.set_child(child)

    def _handle_onboarding_complete(self, reminder_time: str) -> None:
        if self.application is not None and hasattr(self.application, "complete_onboarding"):
            state = self.application.complete_onboarding(reminder_time)
            self.set_state(state)
            self._show_toast("Evening reminder saved")

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
        self._show_toast("Day saved")

    def _show_toast(self, message: str) -> None:
        if Adw is None or not hasattr(self, "_toast_overlay"):
            return
        try:
            toast = Adw.Toast.new(message)
            self._toast_overlay.add_toast(toast)
        except Exception:
            return

    def _build_shell(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        title_block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title = Gtk.Label(label="Pulse")
        title.add_css_class("title-4")
        subtitle = Gtk.Label(label="Burnout monitor for focused work")
        subtitle.add_css_class("caption")
        title_block.append(title)
        title_block.append(subtitle)
        header.set_title_widget(title_block)

        rituals_button = Gtk.MenuButton()
        rituals_button.set_label("Rituals")
        rituals_button.set_popover(self._build_rituals_popover())
        header.pack_end(rituals_button)

        stack = Adw.ViewStack()
        stack.set_vexpand(True)
        stack.add_titled(self._build_dashboard_page(), "dashboard", "Dashboard")
        stack.add_titled(create_evening_page(self._handle_evening_save), "evening", "Evening")
        stack.add_titled(self._build_patterns_page(), "patterns", "Patterns")
        stack.add_titled(self._build_review_page(), "review", "Review")
        stack.set_visible_child_name(self.current_view if self.current_view != "onboarding" else "dashboard")
        toolbar.set_content(stack)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(stack)
        switcher_bar.set_reveal(True)

        root.append(toolbar)
        root.append(switcher_bar)
        return root

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
            view_model = build_dashboard_view_model(burnout, advice, ultradian_cycles=ultradian_cycles)
        else:
            view_model = DashboardViewModel(
                score=50.0,
                score_zone=build_dashboard_view_model(
                    BurnoutScoreResult(score=50.0, ali=0.0, rqs=50.0, trend_penalty=0.0, mbi_correction=0.0),
                    None,
                    ultradian_cycles=0,
                ).score_zone,
                primary_message="No baseline yet. Draw today to start Pulse.",
                primary_action="Open Evening and sketch your day",
                primary_science_ref="Pulse needs a few days of data to become predictive.",
                ultradian_cycles=0,
            )
        return create_dashboard_page(view_model, has_data=has_data)

    def _build_patterns_page(self):
        points = self._load_daily_points(limit=28)
        correlations = self._build_correlation_cards()
        trajectory_scores = self._rolling_burnout_scores()
        view_model = build_patterns_view_model(points, correlations, trajectory_scores)
        return create_patterns_page(view_model)

    def _build_review_page(self):
        points = self._load_daily_points(limit=14)
        this_week = _average_energy(points[-7:])
        previous_week = _average_energy(points[-14:-7])
        mbi_checkin = self._latest_mbi_checkin()
        week_index = date_class.today().isocalendar()[1]
        view_model = build_weekly_review_view_model(
            this_week_average_energy=this_week,
            previous_week_average_energy=previous_week,
            mbi_checkin=mbi_checkin,
            week_index=week_index,
        )
        return create_weekly_review_page(view_model)

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

    def _load_burnout_entries(self, limit: int = 14):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT e.date AS date,
                       AVG(e.level) AS average_energy,
                       c.sleep_hours AS sleep_hours,
                       c.stress_level AS stress_level
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

    def _rolling_burnout_scores(self):
        entries = self._load_burnout_entries(limit=30)
        if len(entries) < 2:
            return []
        latest_mbi = self._latest_mbi_correction()
        scores = []
        for index in range(2, len(entries) + 1):
            scores.append(compute_burnout_score(entries[:index], mbi_correction=latest_mbi))
        return scores[-7:]

    def _build_correlation_cards(self):
        if self.application is None:
            return []
        with self.application.database.connect() as connection:
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
                    label="Sleep vs next-day energy",
                    delta=mean(sleep_high) - mean(sleep_low),
                    condition="after 7+ hours of sleep",
                    science_ref="Sleep and cognitive performance (Walker, 2017)",
                )
            )

        active = [row["average_energy"] for row in data if row["physical_activity"] in ("yes", "some")]
        inactive = [row["average_energy"] for row in data if row["physical_activity"] in ("no", "none", "")]
        if active and inactive:
            cards.append(
                PatternCorrelation(
                    label="Activity vs energy",
                    delta=mean(active) - mean(inactive),
                    condition="on days with movement",
                    science_ref="Recovery cycles (Sonnentag)",
                )
            )

        low_stress = [row["average_energy"] for row in data if row["stress_level"] == "low"]
        high_stress = [row["average_energy"] for row in data if row["stress_level"] == "high"]
        if low_stress and high_stress:
            cards.append(
                PatternCorrelation(
                    label="Stress vs energy",
                    delta=mean(low_stress) - mean(high_stress),
                    condition="on low-stress days",
                    science_ref="Psychological detachment (Sonnentag, 2003)",
                )
            )
        return cards

    def _latest_mbi_correction(self):
        mbi = self._latest_mbi_checkin()
        if mbi is None:
            return 0.0
        return build_weekly_review_view_model(0.0, 0.0, mbi, 0).mbi_correction

    def _latest_mbi_checkin(self):
        if self.application is None:
            return None
        with self.application.database.connect() as connection:
            row = connection.execute(
                """
                SELECT exhaustion, cynicism, efficacy
                FROM mbi_checkins
                ORDER BY date DESC
                LIMIT 1
                """
            ).fetchone()
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


def _average_energy(points):
    if not points:
        return 0.0
    return mean(point.average_energy for point in points)
