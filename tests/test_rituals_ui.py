def test_rituals_page_model_splits_active_and_inactive_items():
    from pulse.ui.rituals import Ritual, build_rituals_page_model

    view_model = build_rituals_page_model(
        [
            Ritual(ritual_id="shutdown", label="Shutdown", time="18:30", active=True),
            Ritual(ritual_id="walk", label="Walk", time="15:00", active=False),
        ]
    )

    assert view_model.title == "Rituals"
    assert [item.label for item in view_model.active_items] == ["Shutdown"]
    assert [item.label for item in view_model.inactive_items] == ["Walk"]
    assert view_model.primary_action == "Save ritual"
    assert view_model.form_style == "plain"
