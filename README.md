# pulse

Pulse is a local-first burnout and energy tracker for GNOME. It is built in Python with GTK4 and Libadwaita, and it stores all data locally in SQLite.

The canonical desktop application ID is `io.github.srpvpn.Pulse`.

## Run

For this stage, run the app directly from the checkout:

```bash
python3 -m pulse.main
```

To preload realistic demo content for UI review and smoke testing:

```bash
python3 -m pulse.main --seed-demo
```

If `python3-gi`, GTK4, or Libadwaita are missing, Pulse still starts in a safe fallback mode for the non-UI paths. The domain logic and tests remain runnable without GTK bindings, but the real desktop UI requires those packages to be installed.

## Test

Use module form for pytest in this environment:

```bash
python3 -m pytest tests -v
```

## Packaging

Circle and Flathub-facing assets live under `data/`, `assets/`, and the top-level Flatpak manifest.

- `data/io.github.srpvpn.Pulse.desktop` is the installable desktop file.
- `data/io.github.srpvpn.Pulse.metainfo.xml` is the AppStream metadata.
- `data/icons/hicolor/scalable/apps/io.github.srpvpn.Pulse.svg` is the current app icon.
- `io.github.srpvpn.Pulse.json` is the primary Flatpak manifest using `org.gnome.Platform` and `org.gnome.Sdk`.
- `assets/screenshots/` stores repository-tracked screenshots referenced by AppStream metadata.

When `appstreamcli` is available locally, validate metadata with:

```bash
appstreamcli validate --strict data/io.github.srpvpn.Pulse.metainfo.xml
```

## Notes

- `pulse/pulse.desktop` remains a checkout-friendly desktop file for development runs.
- The Flatpak manifest is prepared for Flathub-style submission and still needs real `flatpak-builder` validation in a GNOME SDK environment.
- Use `--seed-demo` when validating dashboard, patterns, weekly review, and rituals flows on a fresh checkout.
