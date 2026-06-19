import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promptfloater.paths import get_user_data_dir
from promptfloater.schema import ValidationError
from promptfloater.storage import PromptStore


def document(content="hello"):
    return {
        "categories": [
            {"id": "cat", "name": "工具", "items": [{"id": "item", "content": content}]}
        ]
    }


class PathTests(unittest.TestCase):
    def test_windows_uses_appdata(self):
        result = get_user_data_dir("win32", {"APPDATA": r"C:\Users\me\AppData\Roaming"}, Path("C:/Users/me"))
        self.assertEqual(result, Path(r"C:\Users\me\AppData\Roaming") / "PromptFloater")

    def test_macos_uses_application_support(self):
        result = get_user_data_dir("darwin", {}, Path("/Users/me"))
        self.assertEqual(result, Path("/Users/me/Library/Application Support/PromptFloater"))

    def test_linux_honors_xdg_data_home(self):
        result = get_user_data_dir("linux", {"XDG_DATA_HOME": "/custom/data"}, Path("/home/me"))
        self.assertEqual(result, Path("/custom/data/PromptFloater"))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.user_dir = self.root / "user"
        self.default_file = self.root / "defaults.json"
        self.default_file.write_text(json.dumps(document("default")), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_first_load_migrates_bundled_defaults(self):
        store = PromptStore(self.user_dir, self.default_file)

        result = store.load()

        self.assertEqual(result["categories"][0]["items"][0]["content"], "default")
        self.assertTrue(store.data_file.exists())
        self.assertEqual(json.loads(store.data_file.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_second_save_creates_backup_of_previous_primary(self):
        store = PromptStore(self.user_dir, self.default_file)
        store.save(document("one"))

        store.save(document("two"))

        primary = json.loads(store.data_file.read_text(encoding="utf-8"))
        backup = json.loads(store.backup_file.read_text(encoding="utf-8"))
        self.assertEqual(primary["categories"][0]["items"][0]["content"], "two")
        self.assertEqual(backup["categories"][0]["items"][0]["content"], "one")

    def test_failed_validation_preserves_primary(self):
        store = PromptStore(self.user_dir, self.default_file)
        store.save(document("safe"))
        before = store.data_file.read_bytes()

        with self.assertRaises(ValidationError):
            store.save({"categories": "bad"})

        self.assertEqual(store.data_file.read_bytes(), before)

    def test_replace_failure_preserves_primary(self):
        store = PromptStore(self.user_dir, self.default_file)
        store.save(document("safe"))
        before = store.data_file.read_bytes()

        with patch("promptfloater.storage.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                store.save(document("new"))

        self.assertEqual(store.data_file.read_bytes(), before)

    def test_corrupt_primary_recovers_from_backup(self):
        store = PromptStore(self.user_dir, self.default_file)
        store.save(document("backup"))
        store.save(document("current"))
        store.data_file.write_text("{broken", encoding="utf-8")

        result = store.load()

        self.assertEqual(result["categories"][0]["items"][0]["content"], "backup")
        self.assertEqual(store.data_file.read_text(encoding="utf-8"), "{broken")

    def test_corrupt_primary_and_backup_fall_back_without_overwriting_evidence(self):
        store = PromptStore(self.user_dir, self.default_file)
        self.user_dir.mkdir(parents=True)
        store.data_file.write_text("broken-primary", encoding="utf-8")
        store.backup_file.write_text("broken-backup", encoding="utf-8")

        result = store.load()

        self.assertEqual(result["categories"][0]["items"][0]["content"], "default")
        self.assertEqual(store.data_file.read_text(encoding="utf-8"), "broken-primary")
        self.assertEqual(store.backup_file.read_text(encoding="utf-8"), "broken-backup")

    def test_corrupt_primary_does_not_overwrite_valid_backup_before_failed_replace(self):
        store = PromptStore(self.user_dir, self.default_file)
        store.save(document("backup"))
        store.save(document("current"))
        valid_backup = store.backup_file.read_bytes()
        store.data_file.write_text("broken-primary", encoding="utf-8")

        with patch("promptfloater.storage.os.replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                store.save(document("new"))

        self.assertEqual(store.backup_file.read_bytes(), valid_backup)


if __name__ == "__main__":
    unittest.main()
