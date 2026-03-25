from pathlib import Path
import json
import xml.etree.ElementTree as ET


APP_ID = "io.github.srpvpn.Pulse"
REPO_ROOT = Path(__file__).resolve().parent.parent


def test_default_application_id_matches_packaging_identity(tmp_path):
    from pulse.main import PulseApplication

    app = PulseApplication(data_dir=tmp_path)

    assert app.application_id == APP_ID


def test_development_desktop_entry_uses_packaging_icon_id():
    desktop_path = REPO_ROOT / "pulse" / "pulse.desktop"

    content = desktop_path.read_text(encoding="utf-8")

    assert "Icon={}\n".format(APP_ID) in content


def test_packaging_desktop_file_exists_and_uses_canonical_id():
    desktop_path = REPO_ROOT / "data" / "{}.desktop".format(APP_ID)

    assert desktop_path.exists()
    content = desktop_path.read_text(encoding="utf-8")
    assert "Icon={}\n".format(APP_ID) in content
    assert "StartupWMClass=Pulse\n" in content


def test_metainfo_contains_circle_relevant_core_fields():
    metainfo_path = REPO_ROOT / "data" / "{}.metainfo.xml".format(APP_ID)

    assert metainfo_path.exists()

    root = ET.fromstring(metainfo_path.read_text(encoding="utf-8"))

    assert root.attrib.get("type") == "desktop-application"
    assert root.findtext("id") == APP_ID
    assert root.findtext("name") == "Pulse"
    assert root.findtext("launchable") == "{}.desktop".format(APP_ID)
    assert root.findtext("metadata_license") == "CC0-1.0"
    assert root.findtext("project_license") == "GPL-3.0-or-later"
    assert root.findtext("summary")
    assert root.findtext("url[@type='homepage']")
    assert root.find("screenshots") is not None


def test_packaging_icon_exists():
    icon_path = REPO_ROOT / "data" / "icons" / "hicolor" / "scalable" / "apps" / "{}.svg".format(APP_ID)

    assert icon_path.exists()


def test_repository_includes_screenshot_placeholders_for_appstream_listing():
    screenshot_dir = REPO_ROOT / "assets" / "screenshots"

    assert (screenshot_dir / "burnout-dashboard-dark.png").exists()
    assert (screenshot_dir / "burnout-dashboard-light.png").exists()
    assert (screenshot_dir / "energy-patterns-dark.png").exists()
    assert (screenshot_dir / "energy-patterns-light.png").exists()


def test_flatpak_manifest_targets_gnome_runtime():
    manifest_path = REPO_ROOT / "{}.json".format(APP_ID)

    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["app-id"] == APP_ID
    assert manifest["runtime"] == "org.gnome.Platform"
    assert manifest["runtime-version"] == "49"
    assert manifest["sdk"] == "org.gnome.Sdk"
    assert manifest["command"] == "pulse"
    assert manifest["modules"][0]["sources"][0]["path"] == "./"


def test_repository_has_osi_approved_license_file():
    license_path = REPO_ROOT / "LICENSE"

    assert license_path.exists()
    content = license_path.read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content


def test_readme_mentions_flatpak_and_appstream_readiness():
    readme_path = REPO_ROOT / "README.md"

    content = readme_path.read_text(encoding="utf-8")

    assert "Flatpak" in content
    assert "AppStream" in content
