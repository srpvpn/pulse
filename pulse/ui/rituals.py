"""Ritual scheduling helpers for Pulse."""
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class Ritual:
    ritual_id: str
    label: str
    time: str
    active: bool = True


def due_rituals_for_time(
    rituals: Sequence[Ritual],
    current_time: str,
    delivered_ritual_ids: Sequence[str] = (),
) -> List[Ritual]:
    normalized_now = _normalize_time(current_time)
    delivered = set(delivered_ritual_ids)
    due = []
    for ritual in rituals:
        if not ritual.active:
            continue
        if ritual.ritual_id in delivered:
            continue
        if _normalize_time(ritual.time) <= normalized_now:
            due.append(_normalize_ritual(ritual))
    return sorted(due, key=lambda ritual: (_normalize_time(ritual.time), ritual.label))


def to_rituals(rows: Iterable[object]) -> List[Ritual]:
    rituals = []
    for row in rows:
        rituals.append(
            Ritual(
                ritual_id=str(row["ritual_id"]),
                label=str(row["label"]),
                time=_normalize_time(str(row["time"])),
                active=bool(row["active"]),
            )
        )
    return rituals


def _normalize_ritual(ritual: Ritual) -> Ritual:
    return Ritual(
        ritual_id=ritual.ritual_id,
        label=ritual.label,
        time=_normalize_time(ritual.time),
        active=ritual.active,
    )


def _normalize_time(time_text: str) -> str:
    text = str(time_text).strip()
    if ":" not in text:
        return "20:00"
    hour_text, minute_text = text.split(":", 1)
    try:
        hour = int(hour_text)
        minute = int(minute_text)
    except ValueError:
        return "20:00"
    hour = max(0, min(23, hour))
    minute = max(0, min(59, minute))
    return "{:02d}:{:02d}".format(hour, minute)
