# Command Deck Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish Command Deck with consistent SVG icons, truthful shortcut labels, cleaned category display names, and precise copy confirmation.

**Architecture:** Keep backend and persisted data unchanged. Add fixed SVG factories and display-only normalization in `renderer/app.js`, adjust static icons/CSS in `demo.html`, and lock all four behaviors with renderer regression tests.

**Tech Stack:** HTML/CSS, vanilla JavaScript, Python `unittest`.

---

### Task 1: Add failing polish tests

**Files:**
- Modify: `tests/test_command_deck_ui.py`

- [ ] Assert `svgIcon`, `cleanCategoryName`, `[1]` shortcut rendering, and `item-copy-state` exist.
- [ ] Assert titlebar and tools markup contain fixed SVG rather than character icons.
- [ ] Run the targeted suite and verify it fails for the missing polish behavior.

### Task 2: Implement icons and display normalization

**Files:**
- Modify: `demo.html`
- Modify: `renderer/app.js`

- [ ] Replace static character icons with fixed inline SVG.
- [ ] Add `svgIcon(name)` for favorite, edit, delete, and menu actions.
- [ ] Add `cleanCategoryName(name)` and apply it only during category rendering.
- [ ] Render numeric hints as `[1]`–`[9]`.

### Task 3: Implement copy confirmation and verify

**Files:**
- Modify: `demo.html`
- Modify: `renderer/app.js`
- Modify: `README.md`

- [ ] Add `item-copy-state` and copied-row CSS.
- [ ] Show `COPIED ✓` for 900ms on only the copied row.
- [ ] Run targeted tests, all tests, JS syntax, security scan, desktop smoke test, then commit.
