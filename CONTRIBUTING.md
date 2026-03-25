# Contributing

## Scope

Pulse is a local-first GTK 4 and Libadwaita application for GNOME. Contributions should preserve that direction:
- GTK 4 + Libadwaita only
- GNOME HIG-aligned behavior
- no proprietary runtime requirements
- local-first storage unless there is a strong reason otherwise

## Development Setup

Run from source:

```bash
python3 -m pulse.main
```

Run tests:

```bash
python3 -m pytest tests -v
```

Build the Flatpak locally:

```bash
flatpak-builder --user --install --force-clean --disable-rofiles-fuse --repo=repo builddir io.github.srpvpn.Pulse.json
```

Run the installed Flatpak:

```bash
flatpak run io.github.srpvpn.Pulse
```

## Code Style

- Python, 4 spaces, `snake_case` for functions and variables
- `PascalCase` for classes
- keep modules feature-oriented and reasonably small
- prefer explicit, readable logic over clever shortcuts
- for UI work, keep layouts responsive and use shared helpers from `pulse/ui/theme.py`

## Tests

Behavior changes should include tests whenever practical, especially for:
- onboarding and routing
- database persistence
- empty states and fallback behavior
- Flatpak and metadata regressions

Before opening a change, run:

```bash
python3 -m pytest tests -v
```

## Issues and Merge Requests

When reporting a bug or proposing a change, include:
- what you expected
- what actually happened
- steps to reproduce
- screenshots or screen recordings for UI issues
- the verification commands you ran for code changes

Keep reports factual and technical. All discussion should follow the Code of Conduct.

## Licensing

By contributing to this repository, you agree that your contributions are made under the project license:
- GPL-3.0-or-later

This project does not use a CLA.
