import re
import unittest
from pathlib import Path


class LauncherTests(unittest.TestCase):
    def test_window_uses_transparency_for_shaped_snap_mode(self):
        text = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("transparent=True", text)
        self.assertIn("shadow=False", text)
        self.assertIn("CreateEllipticRgn", text)
        self.assertIn("GetDpiForWindow", text)
        self.assertIn("SetWindowRgn", text)
        self.assertIn("class NativeSnapOverlay", text)
        self.assertIn('attributes("-transparentcolor"', text)
        self.assertIn("SetThreadDpiAwarenessContext", text)
        self.assertIn("screen_width - size", text)
        self.assertIn("vertical_center / sh", text)
        self.assertIn('font=("Consolas", -16, "bold")', text)
        self.assertIn('canvas.bind("<Enter>", schedule_open)', text)
        self.assertIn("root.after(220, open_main)", text)

    def test_windows_launcher_uses_project_virtualenv(self):
        text = Path("启动.bat").read_text(encoding="utf-8")
        self.assertIn(".venv\\Scripts\\python.exe", text)
        self.assertIn(".venv\\Scripts\\pythonw.exe", text)
        self.assertIn("-m venv .venv", text)
        self.assertIn('"%PYTHON%" -m pip install', text)
        self.assertIn('start "" "%PYTHONW%" app.py', text)
        self.assertIn("exit /b 0", text)
        self.assertNotRegex(text, r"(?m)^\s*pip\s")

    def test_windows_hidden_launcher_runs_batch_without_console(self):
        text = Path("启动无黑窗.vbs").read_text(encoding="utf-8")
        self.assertIn('CreateObject("WScript.Shell")', text)
        self.assertIn('"\\启动.bat"', text)
        self.assertIn(", 0, False", text)

    def test_macos_launcher_uses_project_virtualenv(self):
        text = Path("启动.command").read_text(encoding="utf-8")
        self.assertIn(".venv/bin/python3", text)
        self.assertIn("-m venv .venv", text)
        self.assertIn('"$PYTHON" -m pip install', text)
        self.assertNotRegex(text, r"(?m)^\s*pip3?\s")

    def test_requirements_have_compatible_upper_bounds(self):
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"pywebview>=6\.0,<7\.0")
        self.assertRegex(requirements, r"pyperclip>=1\.8,<2\.0")
        self.assertRegex(requirements, r"pyinstaller>=6\.0,<7\.0")

    def test_windows_packaging_script_builds_release_zip(self):
        text = Path("打包-Windows.bat").read_text(encoding="utf-8")
        self.assertIn("PyInstaller", text)
        self.assertIn("taskkill /f /im PromptFloater.exe", text)
        self.assertIn("packaging\\PromptFloater.spec", text)
        self.assertIn("PromptFloater-Windows.zip", text)


if __name__ == "__main__":
    unittest.main()
