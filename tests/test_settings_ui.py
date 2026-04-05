def test_settings_page_model_exposes_language_choices():
    from pulse.ui.settings import build_settings_page_model

    view_model = build_settings_page_model("ru", "dark")

    assert view_model.title == "Настройки"
    assert view_model.language_title == "Язык"
    assert view_model.current_language == "ru"
    assert view_model.language_options == (("en", "English"), ("ru", "Русский"), ("it", "Итальянский"))
    assert view_model.theme_title == "Тема"
    assert view_model.current_theme_mode == "dark"
    assert view_model.theme_options == (
        ("system", "Системная"),
        ("light", "Светлая"),
        ("dark", "Тёмная"),
    )
