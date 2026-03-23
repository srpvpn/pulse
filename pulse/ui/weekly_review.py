"""Weekly review view-model helpers for Pulse."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MBICheckin:
    exhaustion: int
    cynicism: int
    efficacy: int


@dataclass(frozen=True)
class ScienceCard:
    title: str
    body: str
    source: str


@dataclass(frozen=True)
class WeeklyReviewViewModel:
    energy_summary: str
    mbi_correction: float
    science_card: ScienceCard


SCIENCE_CARDS: List[ScienceCard] = [
    ScienceCard(
        title="Ultradian rhythms",
        body="The brain still benefits from alternating focus and recovery blocks across the day.",
        source="Kleitman",
    ),
    ScienceCard(
        title="Psychological detachment",
        body="Switching off work after hours matters because recovery needs actual mental separation.",
        source="Sonnentag",
    ),
    ScienceCard(
        title="Allostatic load",
        body="Repeated stress without recovery accumulates and pushes baseline energy downward.",
        source="McEwen",
    ),
    ScienceCard(
        title="Sleep debt",
        body="Sleep loss compounds across days, so a single short night can distort the next week.",
        source="Walker",
    ),
    ScienceCard(
        title="Cognitive load",
        body="Too many simultaneous demands reduce the energy left for deep work and recovery.",
        source="Sweller",
    ),
    ScienceCard(
        title="Decision fatigue",
        body="Frequent choices drain the reserve that supports focus, patience, and self-control.",
        source="Baumeister",
    ),
    ScienceCard(
        title="Recovery cycles",
        body="Recovery works best when it is repeated, deliberate, and not just passive downtime.",
        source="Sonnentag",
    ),
    ScienceCard(
        title="Autonomy",
        body="Control over schedule and task order protects energy by reducing friction and pressure.",
        source="Self-determination theory",
    ),
    ScienceCard(
        title="Workload mismatch",
        body="When demand stays above capacity, burnout risk climbs even if motivation stays high.",
        source="Job demands-resources",
    ),
    ScienceCard(
        title="Attention residue",
        body="Context switching leaves residue that makes the next task feel harder than it should.",
        source="Leroy",
    ),
]


def build_weekly_review_view_model(
    this_week_average_energy: float,
    previous_week_average_energy: float,
    mbi_checkin: Optional[MBICheckin],
    week_index: int,
) -> WeeklyReviewViewModel:
    energy_summary = "Average energy {this_week:.1f} this week vs {previous_week:.1f} last week ({delta:+.1f})".format(
        this_week=this_week_average_energy,
        previous_week=previous_week_average_energy,
        delta=this_week_average_energy - previous_week_average_energy,
    )
    mbi_correction = compute_mbi_correction(mbi_checkin)
    science_card = SCIENCE_CARDS[week_index % len(SCIENCE_CARDS)]
    return WeeklyReviewViewModel(
        energy_summary=energy_summary,
        mbi_correction=mbi_correction,
        science_card=science_card,
    )


def compute_mbi_correction(mbi_checkin: Optional[MBICheckin]) -> float:
    if mbi_checkin is None:
        return 0.0

    raw_score = mbi_checkin.efficacy - mbi_checkin.exhaustion - mbi_checkin.cynicism
    return _clamp(raw_score / 2.0, -10.0, 10.0)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
