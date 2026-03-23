"""Main window for Pulse."""

from typing import Optional


def _load_adw():
    try:
        import gi

        gi.require_version("Adw", "1")
        from gi.repository import Adw  # type: ignore

        return Adw
    except (ImportError, ValueError):
        return None


Adw = _load_adw()


if Adw is None:
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

    def set_state(self, state: Optional[object]) -> None:
        self.initial_state = state
        self.current_view = getattr(state, "current_view", self.current_view)
        self.reminder_time = getattr(state, "reminder_time", self.reminder_time)
