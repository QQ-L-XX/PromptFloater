import logging
import tempfile
import unittest
from pathlib import Path

from promptfloater.api import AppApi
from promptfloater.logging_setup import setup_logging


VALID = {
    "categories": [
        {"id": "cat", "name": "工具", "items": [{"id": "item", "content": "hello"}]}
    ]
}


class MemoryStore:
    def __init__(self, data=None, error=None):
        self.data = data or VALID
        self.error = error

    def load(self):
        if self.error:
            raise self.error
        return self.data

    def save(self, data):
        if self.error:
            raise self.error
        self.data = data
        return data


class AppApiTests(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(f"promptfloater.test.{id(self)}")
        self.logger.handlers = [logging.NullHandler()]
        self.logger.propagate = False

    def api(self, store=None, clipboard=None):
        return AppApi(store or MemoryStore(), clipboard or (lambda _: None), self.logger)

    def test_get_data_returns_structured_success(self):
        result = self.api().get_data()
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["categories"][0]["id"], "cat")

    def test_validate_import_normalizes_data(self):
        result = self.api().validate_import(VALID)
        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["schema_version"], 1)

    def test_validate_import_reports_invalid_shape(self):
        result = self.api().validate_import({"categories": "bad"})
        self.assertFalse(result["ok"])
        self.assertIn("categories", result["error"])

    def test_save_failure_is_reported(self):
        api = self.api(MemoryStore(error=OSError("disk full")))
        result = api.save_data(VALID)
        self.assertFalse(result["ok"])
        self.assertIn("保存失败", result["error"])

    def test_clipboard_failure_is_reported(self):
        def fail(_):
            raise RuntimeError("clipboard unavailable")

        result = self.api(clipboard=fail).copy_to_clipboard("hello")
        self.assertFalse(result["ok"])
        self.assertIn("复制失败", result["error"])

    def test_false_clipboard_result_is_reported(self):
        result = self.api(clipboard=lambda _: False).copy_to_clipboard("hello")
        self.assertFalse(result["ok"])
        self.assertIn("复制失败", result["error"])

    def test_get_codex_usage_returns_structured_success(self):
        api = AppApi(
            MemoryStore(),
            lambda _: None,
            self.logger,
            codex_usage_provider=lambda: {"available": True, "primary": {"used_percent": 6}},
        )
        result = api.get_codex_usage()
        self.assertTrue(result["ok"])
        self.assertTrue(result["data"]["available"])
        self.assertEqual(result["data"]["primary"]["used_percent"], 6)

    def test_rotating_log_is_created_in_user_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            logger = setup_logging(Path(temp))
            logger.info("hello")
            for handler in logger.handlers:
                handler.flush()
            self.assertTrue((Path(temp) / "logs" / "promptfloater.log").exists())
            self.assertTrue(any(getattr(h, "maxBytes", 0) == 1_048_576 for h in logger.handlers))
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
