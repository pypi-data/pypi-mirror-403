import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "sectra"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache")) / "sectra"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG_FILE)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass
