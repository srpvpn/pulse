def test_patterns_view_model_exposes_empty_guidance_and_insight_title():
    from pulse.ui.patterns import build_patterns_view_model

    view_model = build_patterns_view_model(
        daily_points=[],
        correlations=[],
        trajectory_scores=[],
        selected_range="30D",
    )

    assert view_model.empty_guidance == "Log a few evenings to unlock the weekly heatmap and correlations."
    assert view_model.insight_title == ""
    assert view_model.use_compact_layout is True
    assert view_model.selected_range == "30D"
    assert [item.key for item in view_model.range_options] == ["7D", "30D", "90D", "1Y", "ALL"]
    assert view_model.heatmap_layout == "rhythm"
    assert view_model.rhythm_blocks == []
    assert view_model.rhythm_summary == []
