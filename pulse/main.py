"""Application entry point for Pulse."""

import json
import os
import shutil
import subprocess
import sys
from datetime import date as date_class
from datetime import datetime as datetime_class
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from pulse.db import Database
from pulse.dev_seed import seed_demo_data
from pulse.i18n import normalize_language, tr
from pulse.ui.main_window import PulseMainWindow
from pulse.ui.onboarding import normalize_reminder_time
from pulse.ui.rituals import Ritual, due_rituals_for_time, to_rituals
from pulse.ui.theme import normalize_theme_mode
from pulse.ui.weekly_review import MBICheckin


@dataclass(frozen=True)
class PulseSettings:
    onboarding_complete: bool = False
    reminder_time: str = "20:00"
    language: str = "en"
    theme_mode: str = "system"


@dataclass(frozen=True)
class AppShellState:
    current_view: str
    reminder_time: str
    language: str = "en"
    theme_mode: str = "system"


def _load_gtk():
    try:
        import gi

        gi.require_version("Adw", "1")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Adw  # type: ignore

        return Adw
    except (ImportError, ValueError):
        return None


def _load_gio():
    try:
        import gi

        gi.require_version("Gio", "2.0")
        from gi.repository import Gio  # type: ignore

        return Gio
    except (ImportError, ValueError):
        return None


def _load_glib():
    try:
        import gi

        gi.require_version("GLib", "2.0")
        from gi.repository import GLib  # type: ignore

        return GLib
    except (ImportError, ValueError):
        return None


Adw = _load_gtk()
Gio = _load_gio()
GLib = _load_glib()


def _default_data_dir(application_id: str) -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / application_id
    return Path.home() / ".local" / "share" / application_id


if Adw is None:
    class _FallbackApplication(object):
        def __init__(self, application_id: Optional[str] = None, **kwargs) -> None:
            self.application_id = application_id
            self.kwargs = kwargs
            self.database = None

        def run(self, argv: Optional[Sequence[str]] = None) -> int:
            return 0

        def connect(self, *args, **kwargs) -> None:
            return None

    ApplicationBase = _FallbackApplication
else:
    ApplicationBase = Adw.Application


class PulseApplication(ApplicationBase):
    """GTK application shell for Pulse."""

    def __init__(self, application_id: str = "io.github.srpvpn.Pulse", data_dir: Optional[Path] = None) -> None:
        super(PulseApplication, self).__init__(application_id=application_id)
        self.application_id = application_id
        self.data_dir = Path(data_dir) if data_dir is not None else _default_data_dir(application_id)
        self.settings_path = self.data_dir / "pulse-settings.json"
        self.database = Database(self.data_dir / "pulse.db")
        self._notification_source_id = None
        self.database.initialize()

    def load_settings(self) -> PulseSettings:
        if not self.settings_path.exists():
            return PulseSettings()
        try:
            with self.settings_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, TypeError, AttributeError):
            return PulseSettings()
        if not isinstance(payload, dict):
            return PulseSettings()
        onboarding_complete = payload.get("onboarding_complete", False)
        if not isinstance(onboarding_complete, bool):
            onboarding_complete = False
        return PulseSettings(
            onboarding_complete=onboarding_complete,
            reminder_time=normalize_reminder_time(payload.get("reminder_time", "20:00")),
            language=normalize_language(payload.get("language", "en")),
            theme_mode=normalize_theme_mode(payload.get("theme_mode", "system")),
        )

    def save_settings(self, settings: PulseSettings) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "onboarding_complete": settings.onboarding_complete,
                    "reminder_time": settings.reminder_time,
                    "language": settings.language,
                    "theme_mode": settings.theme_mode,
                },
                handle,
            )

    def build_state(self) -> AppShellState:
        settings = self.load_settings()
        current_view = "evening" if settings.onboarding_complete else "onboarding"
        return AppShellState(
            current_view=current_view,
            reminder_time=settings.reminder_time,
            language=settings.language,
            theme_mode=settings.theme_mode,
        )

    def complete_onboarding(self, reminder_time: str) -> AppShellState:
        settings = PulseSettings(
            onboarding_complete=True,
            reminder_time=normalize_reminder_time(reminder_time),
            language=self.load_settings().language,
            theme_mode=self.load_settings().theme_mode,
        )
        self.save_settings(settings)
        return self.build_state()

    def set_language(self, language: str) -> AppShellState:
        current = self.load_settings()
        self.save_settings(
            PulseSettings(
                onboarding_complete=current.onboarding_complete,
                reminder_time=current.reminder_time,
                language=normalize_language(language),
                theme_mode=current.theme_mode,
            )
        )
        return self.build_state()

    def set_theme_mode(self, theme_mode: str) -> AppShellState:
        current = self.load_settings()
        self.save_settings(
            PulseSettings(
                onboarding_complete=current.onboarding_complete,
                reminder_time=current.reminder_time,
                language=current.language,
                theme_mode=normalize_theme_mode(theme_mode),
            )
        )
        return self.build_state()

    def load_rituals(self) -> List[Ritual]:
        return to_rituals(self.database.list_active_rituals())

    def load_all_rituals(self) -> List[Ritual]:
        return to_rituals(self.database.list_rituals())

    def plan_notifications(
        self,
        current_time: str,
        current_date: Optional[str] = None,
    ) -> List[Ritual]:
        date_text = _resolve_current_date(current_date)
        delivered_ritual_ids = self.database.list_delivered_ritual_ids(date_text)
        return due_rituals_for_time(
            self.load_rituals(),
            current_time,
            delivered_ritual_ids=delivered_ritual_ids,
        )

    def notify_due_rituals(
        self,
        current_time: str,
        current_date: Optional[str] = None,
    ) -> List[Ritual]:
        date_text = _resolve_current_date(current_date)
        due_rituals = self.plan_notifications(current_time=current_time, current_date=date_text)
        language = self.load_settings().language

        for ritual in due_rituals:
            delivered = self._send_ritual_notification(ritual, language)
            if not delivered:
                continue
            self.database.mark_ritual_delivered(
                current_date=date_text,
                ritual_id=ritual.ritual_id,
                delivered_time=current_time,
            )
        return due_rituals

    def do_activate(self):  # pragma: no cover - GTK callback
        try:
            window = PulseMainWindow(application=self, initial_state=self.build_state())
        except RuntimeError:
            return
        if hasattr(window, "present"):
            window.present()
        self._window = window
        self._ensure_notification_scheduler()

    def do_shutdown(self):  # pragma: no cover - GTK callback
        self._stop_notification_scheduler()
        if hasattr(super(PulseApplication, self), "do_shutdown"):
            super(PulseApplication, self).do_shutdown()

    def _ensure_notification_scheduler(self) -> None:
        if self._notification_source_id is not None:
            return
        self._poll_due_ritual_notifications()
        if GLib is None or not hasattr(GLib, "timeout_add_seconds"):
            return
        self._notification_source_id = GLib.timeout_add_seconds(60, self._poll_due_ritual_notifications)

    def _stop_notification_scheduler(self) -> None:
        if self._notification_source_id is None or GLib is None or not hasattr(GLib, "source_remove"):
            self._notification_source_id = None
            return
        GLib.source_remove(self._notification_source_id)
        self._notification_source_id = None

    def _poll_due_ritual_notifications(self) -> bool:
        self.notify_due_rituals(current_time=self._current_time_text())
        return True

    def _current_time_text(self) -> str:
        return datetime_class.now().strftime("%H:%M")

    def _send_ritual_notification(self, ritual: Ritual, language: str) -> bool:
        if self._notify_with_notify_send(ritual, language):
            return True
        return self._notify_with_gio(ritual, language)

    def _notify_with_gio(self, ritual: Ritual, language: str) -> bool:
        if Gio is None or not hasattr(self, "send_notification"):
            return False
        notification = Gio.Notification.new(ritual.label)
        notification.set_body(tr(language, "notification.ritual.body", time=ritual.time))
        if hasattr(notification, "set_default_action"):
            notification.set_default_action("app.activate")
        self.send_notification(ritual.ritual_id, notification)
        return True

    def _notify_with_notify_send(self, ritual: Ritual, language: str) -> bool:
        notify_send_path = shutil.which("notify-send")
        if not notify_send_path:
            return False
        try:
            result = subprocess.run(
                [
                    notify_send_path,
                    "-a",
                    "Pulse",
                    "-i",
                    self.application_id,
                    ritual.label,
                    tr(language, "notification.ritual.body", time=ritual.time),
                ],
                check=False,
            )
        except OSError:
            return False
        return result.returncode == 0


def build_application(data_dir: Optional[Path] = None) -> PulseApplication:
    return PulseApplication(data_dir=data_dir)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(argv if argv is not None else sys.argv)
    application = build_application()
    if "--seed-demo" in arguments:
        seed_demo_data(application.database)
    return application.run(argv)


def _resolve_current_date(current_date: Optional[str]) -> str:
    if current_date:
        return current_date
    return date_class.today().isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
