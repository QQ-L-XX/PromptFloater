"""Validated, atomic persistence for PromptFloater data."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from .schema import validate_document


class PromptStore:
    def __init__(self, user_dir, bundled_file, logger=None):
        self.user_dir = Path(user_dir)
        self.bundled_file = Path(bundled_file)
        self.data_file = self.user_dir / "prompts.json"
        self.backup_file = self.user_dir / "prompts.json.bak"
        self.logger = logger

    def _log_failure(self, message, error):
        if self.logger:
            self.logger.warning(message, exc_info=error)

    @staticmethod
    def _load_file(path):
        with Path(path).open("r", encoding="utf-8") as handle:
            return validate_document(json.load(handle))

    def load(self):
        if self.data_file.exists():
            try:
                return self._load_file(self.data_file)
            except (OSError, ValueError, TypeError) as error:
                self._log_failure("主数据文件读取失败", error)
            if self.backup_file.exists():
                try:
                    return self._load_file(self.backup_file)
                except (OSError, ValueError, TypeError) as error:
                    self._log_failure("备份数据文件读取失败", error)
            return self._load_file(self.bundled_file)

        defaults = self._load_file(self.bundled_file)
        self.save(defaults)
        return defaults

    def save(self, data):
        normalized = validate_document(data)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.user_dir,
                prefix="prompts-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(normalized, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())

            if self.data_file.exists():
                try:
                    self._load_file(self.data_file)
                except (OSError, ValueError, TypeError) as error:
                    self._log_failure("主数据已损坏，不覆盖现有备份", error)
                else:
                    shutil.copy2(self.data_file, self.backup_file)
            os.replace(temporary_path, self.data_file)
            temporary_path = None
            return normalized
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()
