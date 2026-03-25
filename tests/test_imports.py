def test_import_main_module():
    from pulse.main import PulseApplication

    assert PulseApplication is not None


def test_build_application_creates_pulse_application(tmp_path, monkeypatch):
    from pulse.main import PulseApplication, build_application

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
    application = build_application()

    assert isinstance(application, PulseApplication)


def test_build_application_uses_xdg_data_home_for_default_storage(tmp_path, monkeypatch):
    from pulse.main import build_application

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    application = build_application()

    assert application.data_dir == (tmp_path / "xdg-data" / application.application_id)
    assert application.settings_path == application.data_dir / "pulse-settings.json"
