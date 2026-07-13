#!/usr/bin/env python3
"""PromptFloater — 桌面悬浮提示词快速复制工具 (Windows / macOS)"""

import json
import os
import queue
import sys
import threading

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


def set_windows_snap_region(window, snapped, size=0):
    """Clip the native window to a circle without layered-window click bugs."""
    if not IS_WIN or window.native is None:
        return
    import ctypes

    hwnd = int(window.native.Handle.ToInt64())
    if not snapped:
        ctypes.windll.user32.SetWindowRgn(hwnd, 0, True)
        return
    dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    scale = max(1.0, dpi / 96.0) if dpi else 1.0
    physical_size = round(int(size) * scale)
    region = ctypes.windll.gdi32.CreateEllipticRgn(0, 0, physical_size + 1, physical_size + 1)
    if region:
        ctypes.windll.user32.SetWindowRgn(hwnd, region, True)


class NativeSnapOverlay:
    """Small transparent Windows overlay used instead of a WebView snap window."""

    TRANSPARENT = "#010203"

    def __init__(self, on_open):
        self.on_open = on_open
        self.commands = queue.Queue()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def show(self, vertical_ratio, remaining, tone="normal"):
        self.commands.put(("show", float(vertical_ratio), int(remaining), tone))

    def hide(self):
        self.commands.put(("hide",))

    def close(self):
        self.commands.put(("close",))

    def _run(self):
        import ctypes
        import tkinter as tk

        if IS_WIN:
            ctypes.windll.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        size = 72
        root = tk.Tk()
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", self.TRANSPARENT)
        canvas = tk.Canvas(root, width=size, height=size, bg=self.TRANSPARENT,
                           highlightthickness=0, bd=0)
        canvas.pack()
        state = {"angle": 0, "remaining": 0, "tone": "normal", "visible": False}
        hover_job = {"id": None}

        def draw():
            if state["visible"]:
                canvas.delete("all")
                accent = {"normal": "#41f6ff", "warn": "#ffd36b", "hot": "#ff5678"}[state["tone"]]
                angle = state["angle"]
                canvas.create_arc(3, 3, 69, 69, start=angle, extent=112, style="arc",
                                  outline=accent, width=4)
                canvas.create_arc(3, 3, 69, 69, start=angle + 180, extent=82, style="arc",
                                  outline="#ff3bd4", width=4)
                points = [18, 7, 54, 7, 66, 19, 66, 53, 54, 65, 18, 65, 6, 53, 6, 19]
                canvas.create_polygon(points, fill="#071014", outline=accent, width=2)
                inner = [22, 13, 50, 13, 60, 23, 60, 49, 50, 59, 22, 59, 12, 49, 12, 23]
                canvas.create_polygon(inner, fill="#0b1b23", outline="#28505b", width=1)
                scan_y = 19 + int((angle % 36) * 0.8)
                canvas.create_line(15, scan_y, 57, scan_y, fill="#2d8994", width=1)
                canvas.create_text(36, 25, text="CDX", fill="#82aeb5",
                                   font=("Consolas", -7, "bold"))
                canvas.create_text(36, 43, text=f'{state["remaining"]}%', fill=accent,
                                   font=("Consolas", -16, "bold"))
                state["angle"] = (angle + 7) % 360
            root.after(55, draw)

        def poll():
            try:
                while True:
                    command = self.commands.get_nowait()
                    if command[0] == "show":
                        _, vertical_ratio, remaining, tone = command
                        state.update(remaining=remaining, tone=tone, visible=True)
                        screen_width = root.winfo_screenwidth()
                        screen_height = root.winfo_screenheight()
                        x = screen_width - size
                        y = round(vertical_ratio * screen_height - size / 2)
                        y = max(0, min(y, screen_height - size))
                        root.geometry(f"{size}x{size}+{x}+{y}")
                        root.deiconify()
                        root.lift()
                    elif command[0] == "hide":
                        state["visible"] = False
                        root.withdraw()
                    elif command[0] == "close":
                        root.destroy()
                        return
            except queue.Empty:
                pass
            root.after(30, poll)

        def open_main(_event=None):
            if hover_job["id"] is not None:
                root.after_cancel(hover_job["id"])
                hover_job["id"] = None
            state["visible"] = False
            root.withdraw()
            threading.Thread(target=self.on_open, daemon=True).start()

        def schedule_open(_event=None):
            if state["visible"] and hover_job["id"] is None:
                hover_job["id"] = root.after(220, open_main)

        def cancel_open(_event=None):
            if hover_job["id"] is not None:
                root.after_cancel(hover_job["id"])
                hover_job["id"] = None

        canvas.bind("<Button-1>", open_main)
        canvas.bind("<Enter>", schedule_open)
        canvas.bind("<Leave>", cancel_open)
        root.after(30, poll)
        root.after(55, draw)
        root.mainloop()


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
        ww = max(280, min(700, int(geo["w"])))
        wh = max(200, min(900, int(geo["h"])))
        x, y = geo.get("x", sw - ww - 40), geo.get("y", sh - wh - 100)
        x, y = max(0, min(x, sw - 100)), max(0, min(y, sh - 100))
    else:
        ww, wh = 400, 560
        x, y = sw - ww - 40, sh - wh - 100

    state = {"snapped": False, "normal_geo": (ww, wh, x, y), "snap_visible": 64}
    native_overlay = None

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
        min_size=(34, 34),
        background_color=bg,
        transparent=True,
        shadow=False,
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
            if IS_WIN and native_overlay is not None:
                usage = api.get_codex_usage().get("data", {})
                primary = usage.get("primary") or {}
                remaining = round(max(0, 100 - float(primary.get("used_percent", 0))))
                tone = "hot" if remaining <= 10 else "warn" if remaining <= 30 else "normal"
                vertical_center = window.y + window.height / 2
                vertical_ratio = max(0.0, min(vertical_center / sh, 1.0))
                native_overlay.show(vertical_ratio, remaining, tone)
                window.hide()
                state["snapped"] = True
                return True
            window.resize(v, v)
            window.move(sw - v, max(0, min(window.y, sh - v)))
            set_windows_snap_region(window, True, v)
            state["snapped"] = True
            return True
        except Exception:
            return False

    def unsnap_from_edge():
        try:
            if IS_WIN and native_overlay is not None:
                native_overlay.hide()
                w, h, nx, ny = state["normal_geo"]
                window.resize(w, h)
                window.move(nx, ny)
                window.show()
                state["snapped"] = False
                return True
            set_windows_snap_region(window, False)
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
            if native_overlay is not None:
                native_overlay.close()
            window.destroy()
            return True
        except Exception:
            logger.exception("窗口关闭失败")
            return False

    def native_overlay_open_main():
        if unsnap_from_edge():
            window.evaluate_js("window.dispatchEvent(new Event('promptfloater-native-unsnap'))")

    if IS_WIN:
        native_overlay = NativeSnapOverlay(native_overlay_open_main)

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
