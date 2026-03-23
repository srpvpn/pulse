"""Advice rule selection for Pulse."""

from dataclasses import dataclass
from typing import Callable, Optional, Sequence


@dataclass(frozen=True)
class AdviceContext:
    burnout_score: float
    trend: str
    consecutive_low_days: int
    last_sleep: Optional[float]
    sleep_correlation: Optional[float]


@dataclass(frozen=True)
class AdviceRule:
    rule_id: str
    priority: int
    message: str
    action: str
    science_ref: str
    condition: Callable[[AdviceContext], bool]


@dataclass(frozen=True)
class AdviceRecommendation:
    rule_id: str
    priority: int
    message: str
    action: str
    science_ref: str


def select_advice(context: AdviceContext) -> Optional[AdviceRecommendation]:
    matching_rules = [rule for rule in ADVICE_RULES if rule.condition(context)]
    if not matching_rules:
        return None

    rule = max(matching_rules, key=lambda item: item.priority)
    return AdviceRecommendation(
        rule_id=rule.rule_id,
        priority=rule.priority,
        message=rule.message,
        action=rule.action,
        science_ref=rule.science_ref,
    )


ADVICE_RULES: Sequence[AdviceRule] = (
    AdviceRule(
        rule_id="critical_burnout",
        priority=100,
        message="Tonight: your buffer is critically low. No tasks. No decisions.",
        action="Close work apps now",
        science_ref="Allostatic Load (McEwen, 1998)",
        condition=lambda context: context.burnout_score < 30.0 and context.trend == "falling",
    ),
    AdviceRule(
        rule_id="consecutive_low_days",
        priority=80,
        message="3 days below your floor. This is a pattern, not noise.",
        action="Tomorrow morning: one task, no meetings for 90 minutes",
        science_ref="Ultradian Performance Rhythms (Kleitman)",
        condition=lambda context: context.consecutive_low_days >= 3,
    ),
    AdviceRule(
        rule_id="sleep_recovery",
        priority=60,
        message="Your data says sleep is doing real work here.",
        action="Move tomorrow's wake-up 30 minutes earlier than usual",
        science_ref="Sleep and cognitive performance (Walker, 2017)",
        condition=lambda context: (
            context.sleep_correlation is not None
            and context.sleep_correlation > 0.7
            and context.last_sleep is not None
            and context.last_sleep < 6.5
        ),
    ),
)
