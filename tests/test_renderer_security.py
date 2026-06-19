import unittest
from pathlib import Path


class RendererSecurityTests(unittest.TestCase):
    def setUp(self):
        self.html = Path("demo.html").read_text(encoding="utf-8")
        self.script_path = Path("renderer/app.js")
        self.script = self.script_path.read_text(encoding="utf-8") if self.script_path.exists() else ""

    def test_renderer_is_external_and_readable(self):
        self.assertIn('src="renderer/app.js"', self.html)
        self.assertTrue(self.script)

    def test_app_loads_html_from_file_for_relative_assets(self):
        app_source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("url=HTML_FILE", app_source)
        self.assertNotIn("html=main_html", app_source)

    def test_dynamic_user_data_is_not_concatenated_into_inner_html(self):
        combined = self.html + self.script
        self.assertNotIn('data-cid="\'+c.id', combined)
        self.assertNotIn('data-desc="\'+esc(item.desc)', combined)
        self.assertNotIn("category-nav').innerHTML", combined)
        self.assertIn("document.createElement", self.script)
        self.assertIn("replaceChildren", self.script)

    def test_import_is_validated_by_backend(self):
        self.assertIn("validate_import", self.script)
        self.assertIn("await api.validate_import", self.script)

    def test_persist_commits_only_after_success(self):
        self.assertIn("async function persist", self.script)
        self.assertIn("await api.save_data", self.script)
        self.assertIn("if (!result.ok)", self.script)
        self.assertIn("catch (error)", self.script)

    def test_clipboard_async_rejection_has_fallback(self):
        self.assertIn("navigator.clipboard.writeText", self.script)
        self.assertIn(".catch", self.script)
        self.assertIn("textareaCopy", self.script)


if __name__ == "__main__":
    unittest.main()
