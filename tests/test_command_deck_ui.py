import unittest
from pathlib import Path


class CommandDeckUiTests(unittest.TestCase):
    def setUp(self):
        self.html = Path("demo.html").read_text(encoding="utf-8")
        self.script = Path("renderer/app.js").read_text(encoding="utf-8")

    def test_approved_theme_and_shell_are_present(self):
        self.assertIn("--cyan:#41f6ff", self.html.replace(" ", ""))
        self.assertIn("--magenta:#ff3bd4", self.html.replace(" ", ""))
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

    def test_status_shortcuts_are_clickable_actions(self):
        self.assertIn('id="btn-edit-selected"', self.html)
        self.assertIn('id="btn-fav-selected"', self.html)
        self.assertIn('$("#btn-edit-selected").addEventListener("click"', self.script)
        self.assertIn('$("#btn-fav-selected").addEventListener("click"', self.script)

    def test_tools_menu_routes_existing_actions(self):
        self.assertIn("toggleToolsMenu", self.script)
        self.assertIn('data-tool="codex-usage"', self.html)
        self.assertIn('data-tool="export"', self.html)
        self.assertIn('data-tool="import"', self.html)
        self.assertIn('data-tool="categories"', self.html)

    def test_codex_usage_status_card_exists(self):
        self.assertIn('id="codex-usage"', self.html)
        self.assertIn('id="codex-usage-text"', self.html)
        self.assertIn("function refreshCodexUsage", self.script)
        self.assertIn("api.get_codex_usage", self.script)
        self.assertIn("setInterval(refreshCodexUsage, 60000)", self.script)
        self.assertIn("function compactUsage", self.script)
        self.assertIn("function compactRemaining", self.script)
        self.assertIn("5H剩${compactRemaining(snapshot.primary)}", self.script)
        self.assertIn("7D ${usageLabel(snapshot.secondary)}", self.script)
        self.assertIn('id="snap-usage"', self.html)
        self.assertIn('class="snap-aura"', self.html)
        self.assertIn('class="snap-orbit"', self.html)
        self.assertIn("@keyframes holoSpin", self.html)
        self.assertIn("@keyframes deckScan", self.html)
        self.assertIn("@keyframes tickBlink", self.html)
        self.assertIn("@media (max-width:380px)", self.html)
        self.assertIn("@media (max-width:320px)", self.html)
        self.assertIn(".brand-name{display:inline", self.html)
        self.assertNotIn(".status-actions>span{display:none}", self.html)
        self.assertIn("@media (max-height:260px)", self.html)
        self.assertIn("max-height:calc(100% - 16px)", self.html)
        self.assertIn('document.body.classList.toggle("snapped-mode", value)', self.script)
        self.assertIn('document.documentElement.classList.toggle("snapped-mode", value)', self.script)
        self.assertIn(".app-shell.snapped::before,.app-shell.snapped::after", self.html)
        self.assertIn("promptfloater-native-unsnap", self.script)
        self.assertIn("prefers-reduced-motion:reduce", self.html)
        self.assertIn("<strong>CDX</strong>", self.html)
        self.assertIn("100 - Number(windowInfo.used_percent", self.script)
        self.assertIn("100 - Number(snapshot.primary?.used_percent", self.script)

    def test_icons_use_fixed_svg_instead_of_platform_glyphs(self):
        self.assertIn("function svgIcon", self.script)
        self.assertIn("button.append(svgIcon(action))", self.script)
        self.assertNotIn(">◫<", self.html)
        self.assertNotIn(">⌖<", self.html)
        self.assertGreaterEqual(self.html.count("<svg"), 7)

    def test_shortcuts_show_real_single_number_keys(self):
        self.assertIn('shortcut.textContent = index < 9 ? `[${index + 1}]` : ""', self.script)
        self.assertNotIn("⌘${index + 1}", self.script)

    def test_category_emoji_is_removed_only_for_display(self):
        self.assertIn("function cleanCategoryName", self.script)
        self.assertIn("cleanCategoryName(category.name)", self.script)
        self.assertNotIn("category.name = cleanCategoryName", self.script)

    def test_copy_confirmation_is_scoped_to_copied_row(self):
        self.assertIn("item-copy-state", self.script)
        self.assertIn("COPIED ✓", self.script)
        self.assertIn(".prompt-item.copied .item-copy-state", self.html)
        self.assertIn("}, 900)", self.script)


if __name__ == "__main__":
    unittest.main()
