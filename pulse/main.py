"""Application entry point for Pulse."""

from pathlib import Path
from typing import Optional, Sequence

from pulse.db import Database
from pulse.ui.main_window import PulseMainWindow


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
        self.database = Database(self.data_dir / "pulse.db")
        self.database.initialize()

    def do_activate(self):  # pragma: no cover - GTK callback
        window = PulseMainWindow(application=self)
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
