"""Application entry point for Pulse."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from pulse.db import Database
from pulse.ui.main_window import PulseMainWindow
from pulse.ui.onboarding import normalize_reminder_time


@dataclass(frozen=True)
class PulseSettings:
    onboarding_complete: bool = False
    reminder_time: str = "20:00"


@dataclass(frozen=True)
class AppShellState:
    current_view: str
    reminder_time: str


def _load_gtk():
    try:
        import gi

        gi.require_version("Adw", "1")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Adw  # type: ignore

        return Adw
    except (ImportError, ValueError):
        return None


Adw = _load_gtk()


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
        )

    def save_settings(self, settings: PulseSettings) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "onboarding_complete": settings.onboarding_complete,
                    "reminder_time": settings.reminder_time,
                },
                handle,
            )

    def build_state(self) -> AppShellState:
        settings = self.load_settings()
        current_view = "evening" if settings.onboarding_complete else "onboarding"
        return AppShellState(current_view=current_view, reminder_time=settings.reminder_time)

    def complete_onboarding(self, reminder_time: str) -> AppShellState:
        settings = PulseSettings(
            onboarding_complete=True,
            reminder_time=normalize_reminder_time(reminder_time),
        )
        self.save_settings(settings)
        return self.build_state()

    def do_activate(self):  # pragma: no cover - GTK callback
        window = PulseMainWindow(application=self, initial_state=self.build_state())
        if hasattr(window, "present"):
            window.present()
        self._window = window


def build_application(data_dir: Optional[Path] = None) -> PulseApplication:
    return PulseApplication(data_dir=data_dir)


def main(argv: Optional[Sequence[str]] = None) -> int:
    application = build_application()
    return application.run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
