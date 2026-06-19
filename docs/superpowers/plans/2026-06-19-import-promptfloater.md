# PromptFloater Import and Inspection Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the locally created PromptFloater application into this workspace as a clean, reproducible project and verify that its active Python implementation is structurally sound and runnable.

**Architecture:** Preserve the active `pywebview` desktop entry point (`app.py`), browser UI (`demo.html`), persistent JSON data, launch scripts, and supporting Python module. Exclude generated dependencies, caches, nested Git metadata, and one-off reconstruction/debug artifacts; retain legacy Electron source only when it is part of the authored source set, then document which implementation is active.

**Tech Stack:** Python 3, pywebview, pyperclip, HTML/CSS/JavaScript, optional legacy Electron files.

---

### Task 1: Import the authored source tree

**Files:**
- Create: workspace root application files copied from `C:\tmp\prompt-floater`
- Create: `.gitignore`

- [ ] **Step 1: Copy active application and authored support files**

Copy `app.py`, `prompt_floater.py`, `demo.html`, `requirements.txt`, `README.md`, `data/`, launch scripts, renderer assets, and authored Electron compatibility files.

- [ ] **Step 2: Exclude generated and temporary content**

Do not copy `.git/`, `node_modules/`, `__pycache__/`, `_head.html`, `_end.txt`, `_js.txt`, or one-off repair/debug scripts.

- [ ] **Step 3: Add ignore rules**

Add rules for Python caches, virtual environments, Node dependencies, build output, logs, and runtime geometry state.

### Task 2: Verify static integrity

**Files:**
- Test: `app.py`
- Test: `prompt_floater.py`
- Test: `demo.html`
- Test: `data/prompts.json`

- [ ] **Step 1: Compile Python sources**

Run: `python -m py_compile app.py prompt_floater.py`

Expected: exit code 0 with no syntax errors.

- [ ] **Step 2: Validate JSON data**

Run Python's JSON parser over `data/prompts.json` and `data/geometry.json`.

Expected: both files parse successfully.

- [ ] **Step 3: Check JavaScript syntax embedded in the UI**

Extract the inline script from `demo.html` to a temporary file and run `node --check`.

Expected: exit code 0 with no syntax errors.

### Task 3: Verify dependencies and startup path

**Files:**
- Test: `requirements.txt`
- Test: `启动.bat`
- Test: `启动.command`

- [ ] **Step 1: Inspect dependency imports and launcher commands**

Confirm that launchers call the active Python entry point and declared packages match imports.

- [ ] **Step 2: Import application dependencies without opening the GUI**

Run: `python -c "import webview, pyperclip; import app"`

Expected: exit code 0 without creating a window.

- [ ] **Step 3: Perform a bounded startup smoke test**

Launch the application briefly, confirm the process remains alive without immediate exception, then terminate only the process created by the test.

### Task 4: Review code and report findings

**Files:**
- Review: `app.py`
- Review: `prompt_floater.py`
- Review: `demo.html`
- Review: launcher and data files

- [ ] **Step 1: Review security boundaries**

Inspect filesystem access, IPC/API exposure, JSON import/export, clipboard handling, and HTML injection surfaces.

- [ ] **Step 2: Review maintainability and cross-platform behavior**

Identify duplicate implementations, stale files, hard-coded platform assumptions, and packaging gaps.

- [ ] **Step 3: Summarize verified status and concrete issues**

Report what was imported, commands run, pass/fail evidence, and prioritized remediation items without changing behavior beyond the requested import cleanup.
