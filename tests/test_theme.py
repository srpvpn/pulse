def test_theme_exposes_react_app_palette_and_spacing_tokens():
    from pulse.ui.theme import THEME

    assert THEME.sidebar_width == 260
    assert THEME.colors["bg"] == "#F3F4F6"
    assert THEME.colors["accent_soft"] == "#D4EADC"
    assert THEME.radii["card"] == 24
    assert THEME.spacing["section"] == 32


def test_page_layout_specs_keep_pages_centered_and_constrained():
    from pulse.ui.theme import page_layout

    assert page_layout("dashboard").max_width == 1080
    assert page_layout("evening").max_width == 960
    assert page_layout("patterns").max_width == 1120
    assert page_layout("review").max_width == 920
    assert page_layout("rituals").max_width == 820
    assert page_layout("settings").max_width == 720


def test_build_theme_css_uses_distinct_dark_palette():
    from pulse.ui.theme import build_theme_css

    light_css = build_theme_css("light")
    dark_css = build_theme_css("dark")

    assert "#F3F4F6" in light_css
    assert "#FFFFFF" in light_css
    assert "#111827" in light_css
    assert dark_css != light_css
    assert "#F3F4F6" not in dark_css
    assert "#FFFFFF" not in dark_css
    assert "#0F172A" in dark_css
    assert "#111827" in dark_css


def test_build_theme_css_respects_system_palette_preference():
    from pulse.ui.theme import build_theme_css

    system_light_css = build_theme_css("system", prefer_dark=False)
    system_dark_css = build_theme_css("system", prefer_dark=True)

    assert "#F3F4F6" in system_light_css
    assert "#0F172A" in system_dark_css


def test_build_theme_css_supports_high_contrast_palette():
    from pulse.ui.theme import build_theme_css

    light_css = build_theme_css("light")
    high_contrast_css = build_theme_css("light", high_contrast=True)

    assert "outline: 2px solid" not in light_css
    assert "*:focus" not in light_css
    assert "#000000" in high_contrast_css
    assert "#FFFFFF" in high_contrast_css
    assert "#6B7280" not in high_contrast_css
    assert "outline: 2px solid" in high_contrast_css
