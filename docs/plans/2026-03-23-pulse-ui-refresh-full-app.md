# Pulse UI Refresh Full App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the current GTK app into a polished, fully navigable desktop product that keeps all existing backend logic and adopts the visual language of the original design prototype.

**Architecture:** Keep the existing Python + GTK4 + Libadwaita + SQLite stack. Do not port to React. Instead, introduce a shared GTK design system, a custom app shell with a left sidebar and large glass-like cards, then recompose each existing screen on top of the current view-models and database APIs. Close the current feature gaps by wiring weekly review persistence, rituals management, and empty/demo states.

**Tech Stack:** Python 3, GTK4, Libadwaita, sqlite3, pytest

---

### Task 1: Capture The Design System In GTK

**Files:**
- Create: `pulse/ui/theme.py`
- Modify: `pulse/ui/main_window.py`
- Test: `tests/test_theme.py`

**Step 1: Write the failing test**

```python
def test_theme_exposes_react_app_palette_and_spacing_tokens():
    from pulse.ui.theme import THEME

    assert THEME.sidebar_width == 260
    assert THEME.colors["bg"] == "#F3F4F6"
    assert THEME.colors["accent_soft"] == "#D4EADC"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_theme.py -v`
Expected: FAIL because `pulse.ui.theme` does not exist

**Step 3: Write minimal implementation**

Create a shared theme module with palette, spacing, radii, typography scale, card variants, and helper functions for applying CSS classes and inline providers. Match the reference style: soft grey background, dark text, green accent, rounded 24-32px cards, sidebar pills, subtle blur/overlay treatment.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_theme.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/theme.py pulse/ui/main_window.py tests/test_theme.py
git commit -m "feat: add shared GTK design system"
```

### Task 2: Replace The Current Shell With A Styled Navigation Layout

**Files:**
- Modify: `pulse/ui/main_window.py`
- Create: `tests/test_navigation_shell.py`

**Step 1: Write the failing test**

```python
def test_main_window_defaults_to_sidebar_shell_after_onboarding():
    from pulse.main import AppShellState
    from pulse.ui.main_window import PulseMainWindow

    window = PulseMainWindow(application=None, initial_state=AppShellState("dashboard", "20:00"))
    assert window.current_view == "dashboard"
    assert hasattr(window, "_nav_items")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_navigation_shell.py -v`
Expected: FAIL because the custom shell state is missing

**Step 3: Write minimal implementation**

Replace the headerbar + bottom switcher layout with a two-column shell: fixed left sidebar, logo block, section navigation, reminder badge, and right content canvas with decorative background shape. Keep routing in `PulseMainWindow`, but make navigation explicit and reusable.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_navigation_shell.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/main_window.py tests/test_navigation_shell.py
git commit -m "feat: add styled application shell"
```

### Task 3: Redesign Onboarding To Match The New Visual Direction

**Files:**
- Modify: `pulse/ui/onboarding.py`
- Test: `tests/test_app_shell.py`

**Step 1: Write the failing test**

```python
def test_onboarding_keeps_valid_evening_reminder_and_start_action():
    from pulse.ui.onboarding import normalize_reminder_time

    assert normalize_reminder_time("21:30") == "21:30"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_app_shell.py tests/test_onboarding.py -v`
Expected: PASS on old logic, then add assertions for new CTA labels/structure and make it fail

**Step 3: Write minimal implementation**

Keep current onboarding behavior, but rebuild the screen as a hero-first landing page with large title, three glass cards, a premium reminder picker card, and one strong CTA. Reuse the theme module instead of hardcoding per-widget spacing.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_app_shell.py tests/test_onboarding.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/onboarding.py tests/test_app_shell.py tests/test_onboarding.py
git commit -m "feat: redesign onboarding screen"
```

### Task 4: Rebuild Dashboard As The Main Premium Surface

**Files:**
- Modify: `pulse/ui/dashboard.py`
- Modify: `pulse/ui/widgets.py`
- Test: `tests/test_dashboard_viewmodel.py`

**Step 1: Write the failing test**

```python
def test_dashboard_page_handles_empty_and_populated_states():
    from pulse.ui.dashboard import build_dashboard_view_model
    assert build_dashboard_view_model(...) is not None
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dashboard_viewmodel.py -v`
Expected: FAIL after adding assertions for new hero metrics and secondary cards

**Step 3: Write minimal implementation**

Turn the dashboard into the visual reference anchor: oversized score card, zone pill, one insight card, mini metrics row, science note, and latest rituals/today summary cards. Upgrade the score ring styling and empty-state presentation so the app still looks complete without history.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_dashboard_viewmodel.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/dashboard.py pulse/ui/widgets.py tests/test_dashboard_viewmodel.py
git commit -m "feat: redesign dashboard presentation"
```

### Task 5: Make Evening Input Feel Like A Real Product Screen

**Files:**
- Modify: `pulse/ui/evening_input.py`
- Create: `tests/test_evening_input_ui.py`
- Test: `tests/test_evening_input_logic.py`

**Step 1: Write the failing test**

```python
def test_sample_energy_curve_still_returns_hourly_samples_after_ui_refresh():
    from pulse.ui.evening_input import sample_energy_curve
    assert sample_energy_curve([])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_evening_input_logic.py tests/test_evening_input_ui.py -v`
Expected: FAIL in the new UI test because screen metadata and helper API are missing

**Step 3: Write minimal implementation**

Keep the current backend sampling logic, but redesign the page with a larger chart card, visible hour labels, left-side context summary, segmented selectors, a richer note field, validation states, and a sticky save CTA. Add success toasts and post-save route to dashboard.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_evening_input_logic.py tests/test_evening_input_ui.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/evening_input.py tests/test_evening_input_logic.py tests/test_evening_input_ui.py
git commit -m "feat: redesign evening input flow"
```

### Task 6: Upgrade Patterns Into A Readable Analytics Screen

**Files:**
- Modify: `pulse/ui/patterns.py`
- Test: `tests/test_patterns_viewmodel.py`

**Step 1: Write the failing test**

```python
def test_build_patterns_view_model_produces_heatmap_and_correlation_cards():
    from pulse.ui.patterns import build_patterns_view_model
    assert build_patterns_view_model([], [], []).heatmap_caption.startswith("Heatmap")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_patterns_viewmodel.py -v`
Expected: FAIL after adding assertions for new empty-state text and richer card outputs

**Step 3: Write minimal implementation**

Rebuild patterns as a premium analytics page: compact heatmap grid instead of plain rows, trajectory summary card, correlation stack, and “what this means” copy blocks. Preserve the current underlying calculations and keep graceful empty states.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_patterns_viewmodel.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/patterns.py tests/test_patterns_viewmodel.py
git commit -m "feat: redesign patterns screen"
```

### Task 7: Finish Weekly Review By Persisting The Check-In

**Files:**
- Modify: `pulse/db.py`
- Modify: `pulse/ui/weekly_review.py`
- Modify: `pulse/ui/main_window.py`
- Create: `tests/test_weekly_review_persistence.py`
- Test: `tests/test_weekly_review_logic.py`

**Step 1: Write the failing test**

```python
def test_weekly_review_save_persists_latest_mbi_checkin(tmp_path):
    from pulse.db import Database
    db = Database(tmp_path / "pulse.db")
    db.initialize()
    db.save_mbi_checkin("2026-W13", 3, 2, 1)
    assert db.latest_mbi_checkin() is not None
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_weekly_review_logic.py tests/test_weekly_review_persistence.py -v`
Expected: FAIL because save/load APIs are incomplete

**Step 3: Write minimal implementation**

Add explicit database methods for saving and reading weekly MBI check-ins, then wire the weekly review screen so the sliders are not just a preview. Add Save action, prefill from the latest saved values, update dashboard scoring automatically, and show confirmation toast.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_weekly_review_logic.py tests/test_weekly_review_persistence.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/db.py pulse/ui/weekly_review.py pulse/ui/main_window.py tests/test_weekly_review_logic.py tests/test_weekly_review_persistence.py
git commit -m "feat: persist weekly review check-ins"
```

### Task 8: Add A Real Rituals Management Surface

**Files:**
- Modify: `pulse/db.py`
- Modify: `pulse/ui/rituals.py`
- Modify: `pulse/ui/main_window.py`
- Create: `tests/test_rituals_ui.py`
- Test: `tests/test_rituals.py`

**Step 1: Write the failing test**

```python
def test_database_can_deactivate_existing_ritual(tmp_path):
    from pulse.db import Database
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_rituals.py tests/test_rituals_ui.py -v`
Expected: FAIL because there is no management UI and no explicit deactivate/edit path

**Step 3: Write minimal implementation**

Replace the read-only popover with a full screen or side panel for rituals: list cards, add ritual form, time picker, active toggle, and save/update actions. Keep notification logic untouched, but expose all stored ritual functionality through the UI.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_rituals.py tests/test_rituals_ui.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/db.py pulse/ui/rituals.py pulse/ui/main_window.py tests/test_rituals.py tests/test_rituals_ui.py
git commit -m "feat: add rituals management UI"
```

### Task 9: Add Empty States, Demo Seed Data, And Smokeable App Paths

**Files:**
- Modify: `pulse/main.py`
- Create: `pulse/dev_seed.py`
- Create: `tests/test_dev_seed.py`

**Step 1: Write the failing test**

```python
def test_seed_demo_data_creates_entries_for_all_primary_screens(tmp_path):
    from pulse.dev_seed import seed_demo_data
    ...
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_dev_seed.py -v`
Expected: FAIL because no seed helper exists

**Step 3: Write minimal implementation**

Add a small developer/demo seeding helper that populates evening logs, context, rituals, and one weekly check-in. Expose it through a dev-only command or startup flag so the app can always be opened and explored with realistic content. Also add first-run empty cards that explain what each section will show before data exists.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_dev_seed.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/main.py pulse/dev_seed.py tests/test_dev_seed.py
git commit -m "feat: add demo seed data for full-app smoke testing"
```

### Task 10: End-To-End Verification And Manual QA Pass

**Files:**
- Modify: `README.md`
- Create: `docs/plans/2026-03-23-pulse-ui-qa-checklist.md`

**Step 1: Write the verification checklist**

Document exact smoke flows:
- first launch onboarding
- save reminder
- fill evening input
- inspect dashboard
- inspect patterns
- save weekly review
- add/edit ritual
- relaunch and verify persistence

**Step 2: Run automated checks**

Run: `python3 -m pytest tests -v`
Expected: PASS

**Step 3: Run manual smoke app checks**

Run: `python3 -m pulse.main`
Expected: App opens and all primary surfaces are navigable

Run: `python3 -m pulse.main --seed-demo`
Expected: App opens with realistic demo content

**Step 4: Update repository docs**

Add the demo/seed command and verification flow to `README.md`.

**Step 5: Commit**

```bash
git add README.md docs/plans/2026-03-23-pulse-ui-qa-checklist.md
git commit -m "docs: add UI smoke-test workflow"
```

## Implementation Notes

- Treat the original design prototype as a visual reference only, not a structural template.
- Reuse current pure-Python engines and existing tests wherever possible; the UI refresh should not rewrite business logic.
- Prefer adding small UI metadata helpers for testability instead of trying to inspect deep GTK widget trees directly.
- Keep GTK fallback behavior intact where already covered by tests.
- Verify both empty-state and seeded-data paths before calling the app complete.
