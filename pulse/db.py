"""SQLite storage helpers for Pulse."""

from pathlib import Path
from typing import Union


class Database:
    """Minimal database placeholder used by the application shell."""

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
