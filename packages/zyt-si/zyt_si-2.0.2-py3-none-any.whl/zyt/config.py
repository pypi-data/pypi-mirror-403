from pathlib import Path
import platform
import os
def get_config_dir():
    home = Path.home()
    system = platform.system()

    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        base_dir = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base_dir / "zyt"

    elif system == "Darwin":  # macOS
        return home / "Library" / "Application Support" / "zyt"

    else:  # Linux / Unix (XDG)
        xdg = os.environ.get("XDG_CONFIG_HOME")
        return Path(xdg) / "zyt" if xdg else home / ".config" / "zyt"


CONFIG_DIR = get_config_dir()

try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    print("Error: unable to create configuration directory")
    exit(1)

DATA_FILE = CONFIG_DIR / "zyt_data.json"