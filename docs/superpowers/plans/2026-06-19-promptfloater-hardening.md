# PromptFloater Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden PromptFloater without changing its visual design by adding validated, recoverable persistence, safe rendering, explicit errors, isolated launchers, and automated tests.

**Architecture:** Move data validation and persistence into a small `promptfloater` Python package. Keep window control in `app.py`, expose a narrow application API to the WebView, and make the renderer commit state only after backend validation and persistence succeed.

**Tech Stack:** Python 3.11, standard-library `unittest`, pywebview, pyperclip, HTML/CSS/JavaScript, Node.js syntax checks.

---

## File map

- `promptfloater/schema.py`: validate and normalize persisted prompt data.
- `promptfloater/paths.py`: resolve platform user-data paths.
- `promptfloater/storage.py`: migrate, atomically save, back up, and recover data.
- `promptfloater/logging_setup.py`: configure rotating local logs.
- `promptfloater/api.py`: WebView-facing data and clipboard service with structured results.
- `app.py`: window lifecycle and exposure of `AppApi` methods.
- `demo.html`: safe DOM construction and asynchronous save/import behavior.
- `tests/`: schema, storage, API, and renderer security regression tests.
- `requirements.txt`, `启动.bat`, `启动.command`, `README.md`: reproducible setup and documentation.

### Task 1: Data schema validation

**Files:**
- Create: `promptfloater/__init__.py`
- Create: `promptfloater/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write failing schema tests**

Create tests using `unittest` for a valid document, defaulting `schema_version`, normalizing `desc`/`fav`, rejecting a non-object root, non-list categories, duplicate category IDs, duplicate item IDs, missing content, overlong text, and preserving strings containing HTML-like payloads as plain data.

```python
class SchemaTests(unittest.TestCase):
    def test_normalizes_valid_document(self):
        result = validate_document({"categories": [{"id": "c1", "name": "Cat", "items": [{"id": "i1", "content": "hello"}]}]})
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["categories"][0]["items"][0]["fav"], False)

    def test_rejects_duplicate_item_ids(self):
        with self.assertRaisesRegex(ValidationError, "重复"):
            validate_document({"categories": [{"id": "c", "name": "C", "items": [
                {"id": "same", "content": "a"}, {"id": "same", "content": "b"}
            ]}]})
```

- [ ] **Step 2: Run the tests and confirm failure**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_schema -v`

Expected: import failure because `promptfloater.schema` does not exist.

- [ ] **Step 3: Implement schema validation**

Implement `ValidationError`, `validate_document(data)`, and constants limiting the document to 100 categories, 2,000 total items, 120-character names, 200-character descriptions, and 50,000-character prompt contents. Return a newly allocated normalized dictionary and never mutate caller data.

```python
class ValidationError(ValueError):
    pass

def validate_document(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("数据根节点必须是对象")
    categories = data.get("categories")
    if not isinstance(categories, list):
        raise ValidationError("categories 必须是数组")
    # Validate exact field types, uniqueness and limits, then return a copy.
```

- [ ] **Step 4: Run schema tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_schema -v`

Expected: all schema tests pass.

### Task 2: Platform paths and recoverable storage

**Files:**
- Create: `promptfloater/paths.py`
- Create: `promptfloater/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing path and storage tests**

Cover Windows/macOS/Linux path selection with injected platform/environment values; initial migration from bundled defaults; atomic save; `.bak` creation; invalid save preserving the current file; corrupt primary recovery from backup; and fallback to bundled defaults without overwriting corrupt evidence.

```python
def test_failed_validation_preserves_primary(self):
    store = PromptStore(user_dir=self.user_dir, bundled_file=self.default_file)
    store.save(self.valid)
    before = store.data_file.read_bytes()
    with self.assertRaises(ValidationError):
        store.save({"categories": "bad"})
    self.assertEqual(store.data_file.read_bytes(), before)
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_storage -v`

Expected: import failures for `paths` and `storage`.

- [ ] **Step 3: Implement path selection**

Implement `get_user_data_dir(platform_name=None, env=None, home=None)` returning `%APPDATA%\PromptFloater`, `~/Library/Application Support/PromptFloater`, or `$XDG_DATA_HOME/PromptFloater` with `~/.local/share/PromptFloater` fallback.

- [ ] **Step 4: Implement storage**

Implement `PromptStore` with `load()` and `save(data)`. Use `tempfile.NamedTemporaryFile(delete=False, dir=data_dir)`, `flush()`, `os.fsync()`, `shutil.copy2()` for the backup, and `os.replace()` for atomic replacement. `load()` validates primary, then backup, then bundled defaults; migrate defaults only when no primary exists.

- [ ] **Step 5: Run storage tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_storage -v`

Expected: all storage tests pass.

### Task 3: Structured application API and logging

**Files:**
- Create: `promptfloater/api.py`
- Create: `promptfloater/logging_setup.py`
- Create: `tests/test_api.py`
- Modify: `app.py`

- [ ] **Step 1: Write failing API tests**

Test `get_data`, `validate_import`, successful save, failed save returning `{"ok": False, "error": ...}`, and clipboard failure. Use fake stores and clipboard functions; no GUI should open during tests.

```python
def test_save_failure_is_reported(self):
    api = AppApi(FailingStore(), clipboard_copy=lambda _: None)
    result = api.save_data(self.valid)
    self.assertFalse(result["ok"])
    self.assertIn("保存失败", result["error"])
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_api -v`

Expected: import failure because `promptfloater.api` does not exist.

- [ ] **Step 3: Implement API and rotating logging**

Implement `AppApi(store, clipboard_copy)` with structured result dictionaries and `validate_import`. Configure `RotatingFileHandler(maxBytes=1_048_576, backupCount=3, encoding="utf-8")` under the user data directory. Log exception traces but return short Chinese messages.

- [ ] **Step 4: Integrate API into `app.py`**

Create the logger and `PromptStore` before window creation. Expose bound API methods plus the existing window-control closures. Replace bare exceptions with `except (OSError, ValueError, TypeError)` where recovery is expected and `logger.exception(...)` elsewhere. Replace `os._exit(0)` with `window.destroy()`.

- [ ] **Step 5: Run API and existing tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: all tests pass without opening a GUI.

### Task 4: Safe renderer and transactional state updates

**Files:**
- Modify: `demo.html`
- Create: `tests/test_renderer_security.py`

- [ ] **Step 1: Write failing renderer regression tests**

Read `demo.html` as text and assert dynamic rendering uses named element-construction functions, import calls `validate_import`, save awaits the backend result, and the former user-data `innerHTML` templates are absent.

```python
def test_dynamic_user_data_is_not_concatenated_into_inner_html(self):
    html = Path("demo.html").read_text(encoding="utf-8")
    self.assertNotIn("data-cid=\"'+c.id", html)
    self.assertNotIn("data-desc=\"'+esc(item.desc)", html)
    self.assertIn("document.createElement", html)
```

- [ ] **Step 2: Run the renderer test and confirm failure**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_renderer_security -v`

Expected: failures identifying the existing `innerHTML` concatenation and unvalidated import.

- [ ] **Step 3: Replace dynamic HTML construction**

Rewrite category tabs, prompt rows, modal category options, and category management rows with `document.createElement`, `textContent`, safe property assignment, `dataset`, and `replaceChildren`. Static SVG may be created from fixed templates that contain no user data.

- [ ] **Step 4: Make mutations transactional**

Introduce `persist(nextData)` that calls `window.pywebview.api.save_data(nextData)`, checks `result.ok`, commits `S.data` only on success, and reports failure. Build edits on deep-cloned state. Route import through `validate_import`; remove `localStorage` as an authoritative store.

- [ ] **Step 5: Fix asynchronous clipboard fallback**

Use `navigator.clipboard.writeText(...).then(cb).catch(() => textareaFallback(...))` and retain the backend clipboard path as the primary route.

- [ ] **Step 6: Run renderer and full tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 5: Reproducible launchers and documentation

**Files:**
- Modify: `requirements.txt`
- Modify: `启动.bat`
- Modify: `启动.command`
- Modify: `README.md`
- Create: `tests/test_launchers.py`

- [ ] **Step 1: Write failing launcher tests**

Assert both launchers create/use `.venv`, invoke pip through the selected Python interpreter, and never invoke bare `pip`/`pip3`. Assert requirements have upper bounds.

- [ ] **Step 2: Run launcher tests and confirm failure**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_launchers -v`

Expected: failures against the current global-Python launchers and open-ended dependencies.

- [ ] **Step 3: Update launchers and requirements**

Use `.venv\Scripts\pythonw.exe` on Windows and `.venv/bin/python3` on macOS. Create `.venv` with the platform Python when missing, install with `<venv-python> -m pip install -r requirements.txt`, and constrain dependencies to `pywebview>=6.0,<7.0` and `pyperclip>=1.8,<2.0`.

- [ ] **Step 4: Update README**

Document automatic virtual-environment setup, system user-data paths, backups, log location, development test command, and the fact that `data/prompts.json` is bundled defaults.

- [ ] **Step 5: Run launcher and full tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: all tests pass.

### Task 6: Migration and end-to-end verification

**Files:**
- Modify: `data/prompts.json`
- Test: all application files

- [ ] **Step 1: Add schema version to bundled data**

Set the root `schema_version` to `1` without changing the 7 categories or 56 prompt items.

- [ ] **Step 2: Run static verification**

Run Python compilation, JSON validation, bundled Node.js `vm.Script` validation for the inline renderer, `pip check`, and the complete unittest suite.

- [ ] **Step 3: Run an isolated migration smoke test**

Set a temporary `APPDATA`, instantiate `PromptStore`, and verify migration produces a valid user data file containing exactly 7 categories and 56 items.

- [ ] **Step 4: Run a controlled desktop startup smoke test**

Launch `.venv\Scripts\python.exe app.py`, verify the PromptFloater process remains alive for 8 seconds without stderr, then terminate only that test process.

- [ ] **Step 5: Review acceptance criteria**

Confirm invalid imports cannot overwrite data, failed saves preserve the prior file, user data resolves outside the source directory, renderer tests prohibit user-data HTML concatenation, and all existing interactions remain represented in the renderer event bindings.
