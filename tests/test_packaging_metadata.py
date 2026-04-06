from pathlib import Path
import json
import xml.etree.ElementTree as ET


APP_ID = "io.github.srpvpn.pulse"
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
    assert "Categories=GTK;GNOME;Utility;\n" in content


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
    assert root.findtext("url[@type='bugtracker']")
    assert root.findtext("url[@type='contribute']")
    assert root.findtext("url[@type='help']")
    assert root.find("screenshots") is not None
    requires = root.find("requires")
    assert requires is not None
    assert requires.findtext("display_length") == "360"
    recommends = root.find("recommends")
    assert recommends is not None
    control_values = {control.text for control in recommends.findall("control")}
    assert {"keyboard", "pointing"}.issubset(control_values)


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
    assert manifest["runtime-version"] == "50"
    assert manifest["sdk"] == "org.gnome.Sdk"
    assert manifest["command"] == "pulse"
    build_commands = manifest["modules"][0]["build-commands"]
    assert any(
        "$FLATPAK_DEST/share/licenses/$FLATPAK_ID" in command or "/app/share/licenses/io.github.srpvpn.pulse" in command
        for command in build_commands
    )
    source = manifest["modules"][0]["sources"][0]
    assert source["type"] == "archive"
    assert source["url"].startswith("https://github.com/srpvpn/pulse/archive/refs/tags/")
    assert source["url"].endswith(".tar.gz")
    assert len(source["sha256"]) == 64


def test_repository_has_osi_approved_license_file():
    license_path = REPO_ROOT / "LICENSE"

    assert license_path.exists()
    content = license_path.read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in content
    assert "Version 3" in content


def test_repository_has_doap_metadata_file():
    doap_path = REPO_ROOT / "io.github.srpvpn.pulse.doap"

    assert doap_path.exists()

    content = doap_path.read_text(encoding="utf-8")
    assert "<name>Pulse</name>" in content
    assert APP_ID in content


def test_repository_has_ci_workflow():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"

    assert workflow_path.exists()

    content = workflow_path.read_text(encoding="utf-8")
    assert "python3 -m pytest tests -v" in content
    assert "desktop-file-validate data/io.github.srpvpn.pulse.desktop" in content


def test_readme_mentions_flatpak_and_code_of_conduct():
    readme_path = REPO_ROOT / "README.md"

    content = readme_path.read_text(encoding="utf-8")

    assert "Flatpak" in content
    assert "Code of Conduct" in content
