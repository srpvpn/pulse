# Pulse UI QA Checklist

Run automated verification first:

```bash
python3 -m pytest tests -q
```

Manual smoke paths:

1. Launch `python3 -m pulse.main` on a clean data directory and confirm onboarding appears first.
2. Complete onboarding and verify the app routes into the sidebar shell.
3. Open `Evening`, draw a curve, save the day, and confirm the dashboard updates.
4. Open `Patterns` and verify heatmap, trajectory, and empty/data states render.
5. Open `Review`, change MBI sliders, save, and relaunch to confirm persistence.
6. Open `Rituals`, add an active ritual, add an inactive ritual, and confirm both sections update.
7. Launch `python3 -m pulse.main --seed-demo` and confirm all major screens are populated without manual setup.
