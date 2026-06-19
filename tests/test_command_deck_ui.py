import unittest
from pathlib import Path


class CommandDeckUiTests(unittest.TestCase):
    def setUp(self):
        self.html = Path("demo.html").read_text(encoding="utf-8")
        self.script = Path("renderer/app.js").read_text(encoding="utf-8")

    def test_approved_theme_and_shell_are_present(self):
        self.assertIn("--lime:#d6ff62", self.html.replace(" ", ""))
        self.assertIn('id="command-brand"', self.html)
        self.assertIn('id="command-search"', self.html)
        self.assertIn('id="command-status"', self.html)
        self.assertIn('id="tools-menu"', self.html)
        self.assertIn('id="result-count"', self.html)

    def test_icon_buttons_are_accessibly_named(self):
        for element_id in ("btn-snap", "btn-pin", "btn-quit", "btn-tools"):
            start = self.html.index(f'id="{element_id}"')
            excerpt = self.html[start : start + 180]
            self.assertIn("aria-label=", excerpt, element_id)

    def test_selection_state_and_navigation_helpers_exist(self):
        self.assertIn("selectedItemId", self.script)
        self.assertIn("function ensureSelection", self.script)
        self.assertIn("function selectItem", self.script)
        self.assertIn("function selectedItem", self.script)
        self.assertIn("function moveSelection", self.script)
        self.assertIn('scrollIntoView({ block: "nearest" })', self.script)

    def test_balanced_rows_show_title_summary_shortcut_and_selection(self):
        self.assertIn("item-title", self.script)
        self.assertIn("item-summary", self.script)
        self.assertIn("item-shortcut", self.script)
        self.assertIn('row.classList.toggle("selected"', self.script)
        self.assertIn("#result-count", self.script)

    def test_keyboard_contract_and_focus_protection_exist(self):
        self.assertIn("function isTypingTarget", self.script)
        self.assertIn('case "ArrowUp"', self.script)
        self.assertIn('case "ArrowDown"', self.script)
        self.assertIn('case "Enter"', self.script)
        self.assertIn('case "n"', self.script)
        self.assertIn('case "e"', self.script)
        self.assertIn('case "f"', self.script)
        self.assertIn("if (isTypingTarget(event.target))", self.script)

    def test_tools_menu_routes_existing_actions(self):
        self.assertIn("toggleToolsMenu", self.script)
        self.assertIn('data-tool="export"', self.html)
        self.assertIn('data-tool="import"', self.html)
        self.assertIn('data-tool="categories"', self.html)


if __name__ == "__main__":
    unittest.main()
