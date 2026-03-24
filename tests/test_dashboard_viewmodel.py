def test_build_dashboard_view_model_maps_red_zone_and_primary_advice():
    from pulse.advice_engine import AdviceRecommendation
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.dashboard import build_dashboard_view_model

    score = BurnoutScoreResult(
        score=18.0,
        ali=7.5,
        rqs=42.0,
        trend_penalty=60.0,
        mbi_correction=0.0,
    )
    advice = AdviceRecommendation(
        rule_id="critical_burnout",
        priority=100,
        message="Tonight: your buffer is critically low. No tasks. No decisions.",
        action="Close work apps now",
        science_ref="Allostatic Load (McEwen, 1998)",
    )

    view_model = build_dashboard_view_model(score, advice, ultradian_cycles=2)

    assert view_model.score_zone.key == "red"
    assert view_model.score_zone.label == "Critical"
    assert view_model.score_zone.color == "#E24B4A"
    assert view_model.primary_message == advice.message
    assert view_model.primary_action == advice.action
    assert view_model.primary_science_ref == advice.science_ref
    assert view_model.ultradian_cycles == 2


def test_score_zone_for_uses_boundary_values():
    from pulse.ui.dashboard import score_zone_for

    assert score_zone_for(39).key == "red"
    assert score_zone_for(40).key == "yellow"
    assert score_zone_for(69).key == "yellow"
    assert score_zone_for(70).key == "green"


def test_build_dashboard_view_model_uses_fallback_primary_message_when_advice_missing():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.dashboard import build_dashboard_view_model

    score = BurnoutScoreResult(
        score=55.0,
        ali=4.0,
        rqs=68.0,
        trend_penalty=0.0,
        mbi_correction=0.0,
    )

    view_model = build_dashboard_view_model(score, None, ultradian_cycles=1)

    assert view_model.score_zone.key == "yellow"
    assert "attention zone" in view_model.primary_message.lower()
    assert view_model.primary_action == "Keep the afternoon meeting-free"
    assert view_model.primary_science_ref == "Burnout trajectory monitoring"


def test_build_dashboard_view_model_uses_honest_metric_labels():
    from pulse.burnout_engine import BurnoutScoreResult
    from pulse.ui.dashboard import build_dashboard_view_model

    view_model = build_dashboard_view_model(
        BurnoutScoreResult(score=55.0, ali=4.0, rqs=68.0, trend_penalty=0.0, mbi_correction=0.0),
        None,
        ultradian_cycles=1,
    )

    assert [metric.label for metric in view_model.secondary_metrics] == [
        "Recovery quality",
        "Accumulated fatigue",
        "Ultradian cycles",
    ]


def test_score_ring_widget_fallback_tracks_score_and_zone_color():
    from pulse.ui.widgets import create_score_ring_widget

    widget = create_score_ring_widget(score=72.0, zone_color="#1D9E75")

    assert widget.score == 72.0
    assert widget.zone_color == "#1D9E75"
    assert widget.present() is None


def test_score_ring_widget_gtk_path_installs_draw_func_and_queues_redraw(monkeypatch):
    import types

    from pulse.ui import widgets

    draw_calls = []
    queue_calls = []

    class FakeDrawingArea(object):
        def __init__(self):
            self.draw_func = None

        def set_draw_func(self, func):
            self.draw_func = func

        def queue_draw(self):
            queue_calls.append(True)

    fake_gtk = types.SimpleNamespace(DrawingArea=FakeDrawingArea)
    monkeypatch.setattr(widgets, "Gtk", fake_gtk)

    widget = widgets.create_score_ring_widget(score=18.0, zone_color="#E24B4A")

    assert widget.draw_func is not None
    widget.set_score(22.0)
    assert widget.score == 22.0
    assert widget.zone_color == "#E24B4A"
    assert queue_calls == [True]


def test_draw_score_ring_paints_track_and_progress_arc():
    from pulse.ui.widgets import ScoreRingWidget, _draw_score_ring

    calls = []

    class FakeContext(object):
        def set_line_width(self, value):
            calls.append(("line_width", value))

        def set_source_rgba(self, red, green, blue, alpha):
            calls.append(("rgba", round(red, 3), round(green, 3), round(blue, 3), round(alpha, 3)))

        def set_source_rgb(self, red, green, blue):
            calls.append(("rgb", round(red, 3), round(green, 3), round(blue, 3)))

        def arc(self, center_x, center_y, radius, start, end):
            calls.append(("arc", round(center_x, 1), round(center_y, 1), round(radius, 1), round(start, 3), round(end, 3)))

        def stroke(self):
            calls.append(("stroke",))

    widget = ScoreRingWidget(score=50.0, zone_color="#E24B4A")

    _draw_score_ring(widget, FakeContext(), 120, 120)

    assert calls[0] == ("line_width", 8.0)
    assert any(call[0] == "rgba" for call in calls)
    assert any(call[0] == "rgb" for call in calls)
    arc_calls = [call for call in calls if call[0] == "arc"]
    assert len(arc_calls) == 2
    assert arc_calls[1][-2:] == (-1.571, 1.571)
