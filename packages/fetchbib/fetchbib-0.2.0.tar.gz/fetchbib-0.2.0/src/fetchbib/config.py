"""User configuration for fetchbib.

Reads and writes a JSON config file at ~/.config/fetchbib/config.json.
"""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fetchbib"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_EMAIL = "fetchbib@example.com"


def get_email() -> str:
    """Return the configured email, or the default if none is set."""
    cfg = _read_config()
    return cfg.get("email", DEFAULT_EMAIL)


def set_email(email: str) -> None:
    """Persist the email to the config file."""
    cfg = _read_config()
    cfg["email"] = email
    _write_config(cfg)


def _read_config() -> dict:
    """Read the config file, returning an empty dict if it doesn't exist."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def _write_config(cfg: dict) -> None:
    """Write the config dict to disk, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
