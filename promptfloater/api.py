"""Narrow application API exposed to the PromptFloater WebView."""

import logging

from .codex_usage import get_codex_usage
from .schema import ValidationError, validate_document


class AppApi:
    def __init__(self, store, clipboard_copy, logger=None, codex_usage_provider=None):
        self.store = store
        self.clipboard_copy = clipboard_copy
        self.logger = logger or logging.getLogger("promptfloater")
        self.codex_usage_provider = codex_usage_provider or get_codex_usage

    @staticmethod
    def _success(data=None):
        result = {"ok": True}
        if data is not None:
            result["data"] = data
        return result

    def _failure(self, message, error):
        self.logger.exception(message, exc_info=error)
        return {"ok": False, "error": message}

    def get_data(self):
        try:
            return self._success(self.store.load())
        except Exception as error:
            return self._failure("读取提示词失败，请查看日志", error)

    def validate_import(self, data):
        try:
            return self._success(validate_document(data))
        except ValidationError as error:
            self.logger.warning("导入数据校验失败: %s", error)
            return {"ok": False, "error": str(error)}
        except Exception as error:
            return self._failure("导入校验失败，请查看日志", error)

    def save_data(self, data):
        try:
            return self._success(self.store.save(data))
        except ValidationError as error:
            self.logger.warning("保存数据校验失败: %s", error)
            return {"ok": False, "error": f"保存失败：{error}"}
        except Exception as error:
            return self._failure("保存失败，请检查磁盘空间或日志", error)

    def copy_to_clipboard(self, text):
        try:
            if not isinstance(text, str):
                raise TypeError("剪贴板内容必须是字符串")
            copied = self.clipboard_copy(text)
            if copied is False:
                raise RuntimeError("系统剪贴板拒绝写入")
            return self._success()
        except Exception as error:
            return self._failure("复制失败，请手动复制", error)

    def get_codex_usage(self):
        try:
            return self._success(self.codex_usage_provider())
        except Exception as error:
            return self._failure("读取 Codex 用量失败，请查看日志", error)
