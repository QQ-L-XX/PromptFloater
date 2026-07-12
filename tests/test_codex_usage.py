import json
import tempfile
import unittest
from pathlib import Path

from promptfloater.codex_usage import get_codex_usage


def token_event(timestamp, primary_used, primary_reset, secondary_used=0, secondary_reset=0):
    return {
        "timestamp": timestamp,
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {"total_token_usage": {"total_tokens": 123}},
        },
        "rate_limits": {
            "limit_id": "codex",
            "primary": {
                "used_percent": primary_used,
                "window_minutes": 300,
                "resets_at": primary_reset,
            },
            "secondary": {
                "used_percent": secondary_used,
                "window_minutes": 10080,
                "resets_at": secondary_reset,
            },
        },
    }


class CodexUsageTests(unittest.TestCase):
    def test_reads_latest_codex_usage_from_session_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "sessions" / "2026" / "07" / "12"
            log_dir.mkdir(parents=True)
            log = log_dir / "rollout.jsonl"
            log.write_text(
                "\n".join(
                    [
                        json.dumps(token_event("2026-07-12T01:00:00Z", 12, 1783840000)),
                        json.dumps(token_event("2026-07-12T02:00:00Z", 34, 1783843600, 56, 1784440000)),
                    ]
                ),
                encoding="utf-8",
            )

            result = get_codex_usage(temp)

        self.assertTrue(result["available"])
        self.assertEqual(result["limit_id"], "codex")
        self.assertEqual(result["primary"]["used_percent"], 34)
        self.assertEqual(result["primary"]["window_minutes"], 300)
        self.assertEqual(result["primary"]["resets_at"], 1783843600)
        self.assertEqual(result["secondary"]["used_percent"], 56)
        self.assertEqual(result["aggregation"], "max_used_percent_for_current_reset_window")

    def test_aggregates_highest_usage_for_current_reset_window(self):
        with tempfile.TemporaryDirectory() as temp:
            log_dir = Path(temp) / "sessions" / "2026" / "07" / "12"
            log_dir.mkdir(parents=True)
            (log_dir / "older-high.jsonl").write_text(
                json.dumps(token_event("2026-07-12T02:00:00Z", 72, 1783843600, 58, 1784440000)),
                encoding="utf-8",
            )
            (log_dir / "newer-low.jsonl").write_text(
                json.dumps(token_event("2026-07-12T02:01:00Z", 5, 1783843600, 20, 1784440000)),
                encoding="utf-8",
            )

            result = get_codex_usage(temp)

        self.assertTrue(result["available"])
        self.assertEqual(result["primary"]["used_percent"], 72)
        self.assertEqual(result["secondary"]["used_percent"], 58)

    def test_reports_unavailable_when_no_usage_logs_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            result = get_codex_usage(temp)

        self.assertFalse(result["available"])
        self.assertIn("未检测到", result["error"])


if __name__ == "__main__":
    unittest.main()
