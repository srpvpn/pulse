def test_critical_burnout_advice_wins_over_other_matching_rules():
    from pulse.advice_engine import AdviceContext, select_advice

    context = AdviceContext(
        burnout_score=18.0,
        trend="falling",
        consecutive_low_days=4,
        last_sleep=5.5,
        sleep_correlation=0.82,
    )

    advice = select_advice(context)

    assert advice.rule_id == "critical_burnout"
    assert advice.science_ref == "Allostatic Load (McEwen, 1998)"
    assert "Tonight" in advice.message


def test_consecutive_low_days_advice_is_returned_when_critical_threshold_not_met():
    from pulse.advice_engine import AdviceContext, select_advice

    context = AdviceContext(
        burnout_score=42.0,
        trend="stable",
        consecutive_low_days=3,
        last_sleep=7.0,
        sleep_correlation=0.2,
    )

    advice = select_advice(context)

    assert advice.rule_id == "consecutive_low_days"
    assert advice.science_ref == "Ultradian Performance Rhythms (Kleitman)"


def test_select_advice_returns_none_when_no_rule_matches():
    from pulse.advice_engine import AdviceContext, select_advice

    context = AdviceContext(
        burnout_score=72.0,
        trend="rising",
        consecutive_low_days=0,
        last_sleep=7.5,
        sleep_correlation=0.1,
    )

    assert select_advice(context) is None
