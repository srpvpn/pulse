# Pulse V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local-first GNOME desktop app in Python, GTK4, and Libadwaita for energy tracking, burnout analysis, and weekly review.

**Architecture:** The app is split into a thin GTK UI layer, a SQLite storage layer, and pure Python analysis engines for burnout, patterns, and advice. Daily energy curve input is the source of truth; derived score and insights are recomputed from stored data and rendered into a multi-page Adwaita shell.

**Tech Stack:** Python 3.10+, GTK4, Libadwaita, sqlite3, gettext, unittest/pytest-compatible tests

---

### Task 1: Bootstrap Project Layout

**Files:**
- Create: `pulse/__init__.py`
- Create: `pulse/main.py`
- Create: `pulse/db.py`
- Create: `pulse/ui/__init__.py`
- Create: `pulse/ui/main_window.py`
- Create: `pulse/pulse.desktop`
- Test: `tests/test_imports.py`

**Step 1: Write the failing test**

```python
def test_import_main_module():
    from pulse.main import PulseApplication

    assert PulseApplication is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_imports.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing `PulseApplication`

**Step 3: Write minimal implementation**

Create the package skeleton, app entry object, and main window stub with safe GTK imports.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_imports.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse tests
git commit -m "feat: bootstrap pulse application skeleton"
```

### Task 2: Add Database Schema And Repository API

**Files:**
- Modify: `pulse/db.py`
- Test: `tests/test_db.py`

**Step 1: Write the failing test**

```python
def test_initialize_schema_creates_required_tables(tmp_path):
    from pulse.db import Database

    db = Database(tmp_path / "pulse.db")
    db.initialize()

    assert set(db.list_tables()) >= {
        "energy_logs",
        "daily_context",
        "mbi_checkins",
        "burnout_scores",
        "rituals",
        "weekly_notes",
    }
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL because `Database` API is incomplete

**Step 3: Write minimal implementation**

Implement schema creation, connection helpers, and basic upsert/query methods required by engines and UI.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/db.py tests/test_db.py
git commit -m "feat: add sqlite storage layer"
```

### Task 3: Implement Burnout Engine

**Files:**
- Create: `pulse/burnout_engine.py`
- Test: `tests/test_burnout_engine.py`

**Step 1: Write the failing test**

```python
def test_burnout_score_uses_available_inputs_without_mbi():
    from pulse.burnout_engine import compute_burnout_score

    result = compute_burnout_score([...])

    assert 0 <= result.score <= 100
    assert result.mbi_correction == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_burnout_engine.py -v`
Expected: FAIL because the engine does not exist

**Step 3: Write minimal implementation**

Implement ALI, RQS fallback logic, trend penalty, MBI correction, clipping, and helper dataclasses.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_burnout_engine.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/burnout_engine.py tests/test_burnout_engine.py
git commit -m "feat: add burnout scoring engine"
```

### Task 4: Implement Pattern And Advice Engines

**Files:**
- Create: `pulse/pattern_engine.py`
- Create: `pulse/advice_engine.py`
- Test: `tests/test_pattern_engine.py`
- Test: `tests/test_advice_engine.py`

**Step 1: Write the failing tests**

```python
def test_detects_consecutive_low_days():
    ...

def test_prioritizes_critical_burnout_advice():
    ...
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pattern_engine.py tests/test_advice_engine.py -v`
Expected: FAIL because the modules are missing

**Step 3: Write minimal implementation**

Implement daily summaries, trend and correlation helpers, ultradian cycle estimation, science concepts, and rule-priority advice selection.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pattern_engine.py tests/test_advice_engine.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/pattern_engine.py pulse/advice_engine.py tests
git commit -m "feat: add pattern detection and advice rules"
```

### Task 5: Build App Shell And Onboarding

**Files:**
- Modify: `pulse/main.py`
- Modify: `pulse/ui/main_window.py`
- Create: `pulse/ui/onboarding.py`
- Test: `tests/test_app_shell.py`

**Step 1: Write the failing test**

```python
def test_first_launch_routes_to_onboarding(tmp_path):
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_shell.py -v`
Expected: FAIL because onboarding routing is missing

**Step 3: Write minimal implementation**

Add application state bootstrap, settings flag, navigation shell, and onboarding carousel with reminder-time selection.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_shell.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/main.py pulse/ui/main_window.py pulse/ui/onboarding.py tests/test_app_shell.py
git commit -m "feat: add app shell and onboarding flow"
```

### Task 6: Build Dashboard Widgets And Screen

**Files:**
- Create: `pulse/ui/dashboard.py`
- Create: `pulse/ui/widgets.py`
- Test: `tests/test_dashboard_viewmodel.py`

**Step 1: Write the failing test**

```python
def test_dashboard_viewmodel_exposes_single_primary_insight():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dashboard_viewmodel.py -v`
Expected: FAIL because dashboard mapping does not exist

**Step 3: Write minimal implementation**

Create score ring drawing widget, dashboard view model helpers, insight/advice card composition, and red-zone simplification behavior.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dashboard_viewmodel.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/dashboard.py pulse/ui/widgets.py tests/test_dashboard_viewmodel.py
git commit -m "feat: add burnout dashboard"
```

### Task 7: Build Evening Input And Curve Sampling

**Files:**
- Create: `pulse/ui/evening_input.py`
- Modify: `pulse/db.py`
- Test: `tests/test_evening_input_logic.py`

**Step 1: Write the failing test**

```python
def test_curve_samples_hourly_points_from_drag_path():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_evening_input_logic.py -v`
Expected: FAIL because curve sampling logic is absent

**Step 3: Write minimal implementation**

Implement drawing-area controller logic, spline interpolation helpers, hourly sampling, context form binding, and save/recompute flow.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_evening_input_logic.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/evening_input.py pulse/db.py tests/test_evening_input_logic.py
git commit -m "feat: add evening energy curve input"
```

### Task 8: Build Patterns And Weekly Review Screens

**Files:**
- Create: `pulse/ui/patterns.py`
- Create: `pulse/ui/weekly_review.py`
- Test: `tests/test_patterns_viewmodel.py`
- Test: `tests/test_weekly_review_logic.py`

**Step 1: Write the failing tests**

```python
def test_patterns_viewmodel_formats_correlations():
    ...

def test_weekly_review_generates_summary_and_science_card():
    ...
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_patterns_viewmodel.py tests/test_weekly_review_logic.py -v`
Expected: FAIL because the screens are not implemented

**Step 3: Write minimal implementation**

Implement heatmap rendering, correlation cards, burnout trajectory data mapping, weekly summary form, MBI check-in handling, and science-card rotation.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_patterns_viewmodel.py tests/test_weekly_review_logic.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/ui/patterns.py pulse/ui/weekly_review.py tests
git commit -m "feat: add patterns and weekly review screens"
```

### Task 9: Add Rituals And Notifications

**Files:**
- Create: `pulse/ui/rituals.py`
- Modify: `pulse/main.py`
- Modify: `pulse/db.py`
- Test: `tests/test_rituals.py`

**Step 1: Write the failing test**

```python
def test_due_ritual_detection_finds_active_reminders_for_today():
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_rituals.py -v`
Expected: FAIL because ritual scheduling is not implemented

**Step 3: Write minimal implementation**

Add rituals CRUD, due-check logic, notification dispatch, startup missed-ritual detection, and rituals preferences page.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_rituals.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pulse/main.py pulse/db.py pulse/ui/rituals.py tests/test_rituals.py
git commit -m "feat: add rituals and notifications"
```

### Task 10: Final Integration And Verification

**Files:**
- Modify: `README.md`
- Modify: `pulse/pulse.desktop`
- Test: `tests/`

**Step 1: Write the failing integration check**

Document the exact launch command and any missing runtime prerequisites in `README.md`, then add or adjust tests for integration gaps found during manual launch.

**Step 2: Run focused verification**

Run: `pytest -v`
Expected: PASS

**Step 3: Run application smoke test**

Run: `python -m pulse.main`
Expected: Application starts or prints clear GTK dependency guidance if GTK bindings are unavailable

**Step 4: Refactor and polish**

Tighten gettext usage, toasts, CSS hooks, and onboarding defaults without changing validated behavior.

**Step 5: Commit**

```bash
git add README.md pulse/pulse.desktop pulse tests
git commit -m "feat: ship pulse v1 desktop app"
```
