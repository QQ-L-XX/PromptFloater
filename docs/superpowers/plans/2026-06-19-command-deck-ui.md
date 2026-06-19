# Command Deck UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild PromptFloater's renderer as the approved B2 balanced-density Command Deck with lime accents and practical keyboard navigation while preserving all backend behavior.

**Architecture:** Keep `app.py` and the persistence API unchanged. Modify the static shell in `demo.html`, centralize selection and keyboard behavior in `renderer/app.js`, and extend Python regression tests to verify structure, safe rendering, focus protection, and shortcut contracts.

**Tech Stack:** HTML/CSS, vanilla JavaScript, Python `unittest`, pywebview.

---

### Task 1: Lock the Command Deck visual contract with tests

**Files:**
- Create: `tests/test_command_deck_ui.py`
- Test: `demo.html`
- Test: `renderer/app.js`

- [ ] **Step 1: Write failing visual-contract tests**

Assert that the HTML exposes `command-brand`, `command-search`, `command-status`, `tools-menu`, and lime theme variables. Assert that the renderer uses `selectedItemId`, `ensureSelection`, `moveSelection`, `scrollIntoView`, `isTypingTarget`, and a `keydown` handler for `ArrowUp`, `ArrowDown`, `Enter`, `n`, `e`, and `f`.

- [ ] **Step 2: Run and verify RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_command_deck_ui -v`

Expected: failures because the Command Deck DOM and state do not yet exist.

### Task 2: Rebuild the static shell and theme

**Files:**
- Modify: `demo.html`
- Test: `tests/test_command_deck_ui.py`

- [ ] **Step 1: Replace theme tokens and layout styles**

Define the approved neutral-black palette with `--lime: #d6ff62`, compact 120–220 ms transitions, monospaced metadata, 40 px title bar, 38 px command search, balanced two-line list rows, numbered category tabs, and compact status bar.

- [ ] **Step 2: Update static markup**

Add the `PF / COMMAND DECK` brand, command-search hint, tools trigger/menu, shortcut status labels, result counter, and accessible labels for icon-only controls. Preserve existing IDs used by the renderer where practical.

- [ ] **Step 3: Run visual-contract tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_command_deck_ui -v`

Expected: markup/theme tests pass; JavaScript selection tests remain failing.

### Task 3: Add shared selection state and balanced rows

**Files:**
- Modify: `renderer/app.js`
- Test: `tests/test_command_deck_ui.py`
- Test: `tests/test_renderer_security.py`

- [ ] **Step 1: Add selection state helpers**

Add `selectedItemId`, `ensureSelection()`, `selectedItem()`, `selectItem(id)`, and `moveSelection(direction)`. Selection must follow filtered order, wrap at list boundaries, and call `scrollIntoView({block: "nearest"})` after rendering.

- [ ] **Step 2: Render Command Deck rows**

Render a short title derived from the first content line, a one-line summary, the visible item number, `⌘1`–`⌘9` hints, and favorite state. Apply `.selected` to the shared selection and update the result counter.

- [ ] **Step 3: Synchronize selection with search, categories, and mouse**

Search and category changes select the first visible result. Mouse hover/click updates `selectedItemId`; copying and editing operate on the same item.

- [ ] **Step 4: Run renderer tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_command_deck_ui tests.test_renderer_security -v`

Expected: selection and safe-rendering tests pass.

### Task 4: Implement practical shortcut layer and tools menu

**Files:**
- Modify: `renderer/app.js`
- Modify: `demo.html`
- Test: `tests/test_command_deck_ui.py`

- [ ] **Step 1: Add focus protection**

Implement `isTypingTarget(target)` for `INPUT`, `TEXTAREA`, `SELECT`, and `contentEditable`; global shortcuts must return early while typing except for Escape and the existing save combination.

- [ ] **Step 2: Add keyboard actions**

Implement `/`, `ArrowUp`, `ArrowDown`, `Enter`, `1`–`9`, `N`, `E`, `F`, and layered Escape behavior exactly as the approved specification.

- [ ] **Step 3: Add tools menu behavior**

Move import, export, and category management behind the compact `···` trigger. Close the menu on outside click and Escape without changing existing action implementations.

- [ ] **Step 4: Run Command Deck tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_command_deck_ui -v`

Expected: all Command Deck tests pass.

### Task 5: Documentation and full verification

**Files:**
- Modify: `README.md`
- Test: all project files

- [ ] **Step 1: Document UI and shortcuts**

Add the Command Deck shortcut table and explain keyboard selection, tools menu, and mouse compatibility.

- [ ] **Step 2: Run complete verification**

Run all 35 existing tests plus new Command Deck tests, Python compilation, JSON schema validation, `pip check`, JavaScript syntax checking, forbidden-pattern scan, and a controlled 8-second desktop startup smoke test.

- [ ] **Step 3: Inspect the rendered desktop process**

Confirm a responsive `PromptFloater` window is created, user data remains in AppData, logs are created, and no stderr is emitted.

- [ ] **Step 4: Commit the implementation**

Run: `git add demo.html renderer/app.js tests/test_command_deck_ui.py README.md docs/superpowers/plans/2026-06-19-command-deck-ui.md && git commit -m "feat: redesign PromptFloater as Command Deck"`
