#!/usr/bin/env python3
"""PromptFloater — 桌面悬浮提示词快速复制工具 (Windows / macOS)"""

import json
import os
import sys

import webview

from promptfloater.api import AppApi
from promptfloater.logging_setup import setup_logging
from promptfloater.paths import get_user_data_dir
from promptfloater.storage import PromptStore

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "demo.html")
BUNDLED_DATA_FILE = os.path.join(BASE_DIR, "data", "prompts.json")


def load_geometry(user_data_dir, logger):
    try:
        gf = os.path.join(user_data_dir, "geometry.json")
        if os.path.exists(gf):
            with open(gf, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError, TypeError):
        logger.exception("窗口位置读取失败")
    return None


def single_instance_lock():
    """Cross-platform single-instance check."""
    if IS_WIN:
        import ctypes
        try:
            mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "PromptFloater_SI")
            if ctypes.windll.kernel32.GetLastError() == 183:
                ctypes.windll.user32.MessageBoxW(0, "PromptFloater 已在运行中", "提示", 0x40)
                sys.exit(0)
        except Exception:
            pass  # fallback
    else:
        # macOS / Linux: PID file lock
        import tempfile
        lockfile = os.path.join(tempfile.gettempdir(), "promptfloater.lock")
        if os.path.exists(lockfile):
            try:
                with open(lockfile, "r") as f:
                    old_pid = int(f.read().strip())
                # Check if process still alive
                os.kill(old_pid, 0)
                print("PromptFloater 已在运行中")
                sys.exit(0)
            except (OSError, ValueError):
                os.remove(lockfile)
        with open(lockfile, "w") as f:
            f.write(str(os.getpid()))


def get_screen_size():
    """Cross-platform screen size detection."""
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        r.destroy()
        return sw, sh
    except Exception:
        # Fallback for headless or tkinter-less environments
        return 1920, 1080


def copy_to_clipboard(text):
    """Cross-platform clipboard copy."""
    # Try pyperclip first (most reliable cross-platform)
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        pass

    # Fallback to tkinter
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        return True
    except Exception:
        return False


def main():
    single_instance_lock()

    user_data_dir = get_user_data_dir()
    logger = setup_logging(user_data_dir)
    store = PromptStore(user_data_dir, BUNDLED_DATA_FILE, logger)
    api = AppApi(store, copy_to_clipboard, logger)

    if not os.path.exists(HTML_FILE):
        print(f"ERROR: {HTML_FILE} not found!")
        sys.exit(1)

    sw, sh = get_screen_size()

    # Saved or default geometry
    geo = load_geometry(user_data_dir, logger)
    if geo and geo.get("w") and geo.get("h"):
        ww, wh = geo["w"], geo["h"]
        x, y = geo.get("x", sw - ww - 40), geo.get("y", sh - wh - 100)
        x, y = max(0, min(x, sw - 100)), max(0, min(y, sh - 100))
    else:
        ww, wh = 400, 560
        x, y = sw - ww - 40, sh - wh - 100

    state = {"snapped": False, "normal_geo": (ww, wh, x, y), "snap_visible": 28}

    # On macOS, use a slightly different background to match vibrancy
    bg = "#0d0d14"

    window = webview.create_window(
        title="PromptFloater",
        url=HTML_FILE,
        width=ww,
        height=wh,
        x=x,
        y=y,
        frameless=True,
        on_top=True,
        easy_drag=False,
        resizable=True,
        min_size=(28, 28),
        background_color=bg,
    )

    def get_geometry():
        try:
            return {
                "x": window.x, "y": window.y,
                "w": window.width, "h": window.height,
                "screen_w": sw, "screen_h": sh,
                "snapped": state["snapped"],
            }
        except Exception:
            return {"x": 0, "y": 0, "w": 400, "h": 560,
                    "screen_w": sw, "screen_h": sh, "snapped": False}

    def save_geometry(w, h, x, y):
        try:
            gf = os.path.join(user_data_dir, "geometry.json")
            os.makedirs(os.path.dirname(gf), exist_ok=True)
            with open(gf, "w", encoding="utf-8") as f:
                json.dump({"w": w, "h": h, "x": x, "y": y}, f)
            return True
        except (OSError, TypeError, ValueError):
            logger.exception("窗口位置保存失败")
            return False

    # ── Window control ──────────────────────────────────────
    def move_window(dx, dy):
        try:
            window.move(window.x + int(dx), window.y + int(dy))
        except (TypeError, ValueError):
            logger.warning("忽略无效窗口移动参数: %r, %r", dx, dy)

    def resize_window(w, h):
        try:
            w = max(280, min(700, int(w)))
            h = max(200, min(900, int(h)))
            window.resize(w, h)
            if not state["snapped"]:
                state["normal_geo"] = (w, h, window.x, window.y)
        except (TypeError, ValueError):
            logger.warning("忽略无效窗口尺寸参数: %r, %r", w, h)

    def snap_to_edge():
        try:
            state["normal_geo"] = (window.width, window.height, window.x, window.y)
            v = state["snap_visible"]
            window.resize(v, v)
            window.move(sw - v, max(0, min(window.y, sh - v)))
            state["snapped"] = True
            return True
        except Exception:
            return False

    def unsnap_from_edge():
        try:
            w, h, nx, ny = state["normal_geo"]
            window.resize(w, h)
            window.move(nx, ny)
            state["snapped"] = False
            return True
        except Exception:
            return False

    def hide_taskbar_icon():
        """Hide from taskbar. Windows-only via ctypes, no-op on Mac."""
        if not IS_WIN:
            return False
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "PromptFloater")
            if hwnd:
                GWL_EXSTYLE = -20
                ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ex |= 0x80      # WS_EX_TOOLWINDOW
                ex &= ~0x40000  # WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0, 0x20 | 0x2 | 0x1 | 0x4
                )
                return True
        except Exception:
            pass
        return False

    def quit_app():
        try:
            window.destroy()
            return True
        except Exception:
            logger.exception("窗口关闭失败")
            return False

    # ── Expose to JS ────────────────────────────────────────
    window.expose(
        api.copy_to_clipboard,
        api.get_codex_usage,
        api.get_data,
        api.save_data,
        api.validate_import,
        get_geometry,
        move_window,
        resize_window,
        snap_to_edge,
        unsnap_from_edge,
        hide_taskbar_icon,
        save_geometry,
        quit_app,
    )

    # pywebview uses Edge WebView2 on Windows, WKWebView on macOS
    webview.start(debug=False, http_server=True)


if __name__ == "__main__":
    main()
