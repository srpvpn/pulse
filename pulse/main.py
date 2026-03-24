"""Application entry point for Pulse."""

import json
import sys
from datetime import date as date_class
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from pulse.db import Database
from pulse.dev_seed import seed_demo_data
from pulse.i18n import normalize_language
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


Adw = _load_gtk()
Gio = _load_gio()


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

    def __init__(self, application_id: str = "com.example.Pulse", data_dir: Optional[Path] = None) -> None:
        super(PulseApplication, self).__init__(application_id=application_id)
        self.application_id = application_id
        self.data_dir = Path(data_dir) if data_dir is not None else Path.cwd()
        self.settings_path = self.data_dir / "pulse-settings.json"
        self.database = Database(self.data_dir / "pulse.db")
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

        for ritual in due_rituals:
            self.database.mark_ritual_delivered(
                current_date=date_text,
                ritual_id=ritual.ritual_id,
                delivered_time=current_time,
            )
            if Gio is None:
                continue
            if hasattr(self, "send_notification"):
                notification = Gio.Notification.new(ritual.label)
                notification.set_body("Time for {}".format(ritual.label))
                self.send_notification(ritual.ritual_id, notification)
        return due_rituals

    def do_activate(self):  # pragma: no cover - GTK callback
        try:
            window = PulseMainWindow(application=self, initial_state=self.build_state())
        except RuntimeError:
            return
        if hasattr(window, "present"):
            window.present()
        self._window = window


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
