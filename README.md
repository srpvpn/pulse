# pulse

Pulse is a local-first burnout and energy tracker for GNOME. It is built in Python with GTK4 and Libadwaita, and it stores all data locally in SQLite.

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

## Notes

- The current desktop entry is for development use from this repository checkout.
- There is no packaged Flatpak or `.deb` in this repository yet.
- Use `--seed-demo` when validating dashboard, patterns, weekly review, and rituals flows on a fresh checkout.
