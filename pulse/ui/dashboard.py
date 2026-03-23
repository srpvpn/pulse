"""Dashboard view-model helpers for Pulse."""

from dataclasses import dataclass
from typing import Optional

from pulse.advice_engine import AdviceRecommendation
from pulse.burnout_engine import BurnoutScoreResult


@dataclass(frozen=True)
class DashboardScoreZone:
    key: str
    label: str
    color: str
    minimum: int
    maximum: int


@dataclass(frozen=True)
class DashboardViewModel:
    score: float
    score_zone: DashboardScoreZone
    primary_message: str
    primary_action: str
    primary_science_ref: str
    ultradian_cycles: int


RED_ZONE = DashboardScoreZone("red", "Critical", "#E24B4A", 0, 39)
YELLOW_ZONE = DashboardScoreZone("yellow", "Attention", "#EF9F27", 40, 69)
GREEN_ZONE = DashboardScoreZone("green", "Healthy", "#1D9E75", 70, 100)


def score_zone_for(score: float) -> DashboardScoreZone:
    if score <= RED_ZONE.maximum:
        return RED_ZONE
    if score <= YELLOW_ZONE.maximum:
        return YELLOW_ZONE
    return GREEN_ZONE


def build_dashboard_view_model(
    burnout: BurnoutScoreResult,
    advice: Optional[AdviceRecommendation],
    ultradian_cycles: int = 0,
) -> DashboardViewModel:
    score_zone = score_zone_for(burnout.score)
    primary_message, primary_action, primary_science_ref = _primary_advice(score_zone, advice)
    return DashboardViewModel(
        score=burnout.score,
        score_zone=score_zone,
        primary_message=primary_message,
        primary_action=primary_action,
        primary_science_ref=primary_science_ref,
        ultradian_cycles=ultradian_cycles,
    )


def _primary_advice(
    score_zone: DashboardScoreZone,
    advice: Optional[AdviceRecommendation],
) -> tuple:
    if advice is not None:
        return advice.message, advice.action, advice.science_ref

    if score_zone.key == "red":
        return (
            "Your score is in the critical zone. Stop adding load today.",
            "Close work apps now",
            "Allostatic Load (McEwen, 1998)",
        )
    if score_zone.key == "yellow":
        return (
            "Your score is in the attention zone. Protect the next block of work.",
            "Keep the afternoon meeting-free",
            "Burnout trajectory monitoring",
        )
    return (
        "Your score is in the healthy zone. Keep the load stable.",
        "Continue with the current plan",
        "Recovery and pacing",
    )
