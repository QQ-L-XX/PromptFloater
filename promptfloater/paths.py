"""Platform-specific PromptFloater paths."""

import os
import sys
from pathlib import Path


def get_user_data_dir(platform_name=None, env=None, home=None):
    platform_name = platform_name or sys.platform
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)

    if platform_name == "win32":
        base = Path(env.get("APPDATA") or (home / "AppData" / "Roaming"))
    elif platform_name == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(env.get("XDG_DATA_HOME") or (home / ".local" / "share"))
    return base / "PromptFloater"

