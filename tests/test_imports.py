def test_import_main_module():
    from pulse.main import PulseApplication

    assert PulseApplication is not None


def test_build_application_creates_pulse_application():
    from pulse.main import PulseApplication, build_application

    application = build_application()

    assert isinstance(application, PulseApplication)
