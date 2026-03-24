def test_translate_returns_russian_copy_for_known_key():
    from pulse.i18n import tr

    assert tr("ru", "nav.dashboard") == "Панель"
    assert tr("en", "nav.dashboard") == "Dashboard"
