"""User configuration for fetchbib.

Reads and writes a JSON config file at ~/.config/fetchbib/config.json.
"""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fetchbib"
CONFIG_FILE = CONFIG_DIR / "config.json"

OPENALEX_API_KEY_ENV = "OPENALEX_API_KEY"


def get_openalex_api_key() -> str | None:
    """Return the OpenAlex API key, checking env var first, then config file.

    Returns None if no key is configured.
    """
    env_key = os.environ.get(OPENALEX_API_KEY_ENV)
    if env_key:
        return env_key
    cfg = _read_config()
    return cfg.get("openalex_api_key")


def set_openalex_api_key(key: str) -> None:
    """Persist the OpenAlex API key to the config file."""
    cfg = _read_config()
    cfg["openalex_api_key"] = key
    _write_config(cfg)


def get_protect_titles() -> bool:
    """Return True if titles should be double-braced."""
    cfg = _read_config()
    return cfg.get("protect_titles", False)


def set_protect_titles(enabled: bool) -> None:
    """Persist the protect_titles setting."""
    cfg = _read_config()
    cfg["protect_titles"] = enabled
    _write_config(cfg)


def get_exclude_issn() -> bool:
    """Return True if ISSN should be excluded from BibTeX entries."""
    cfg = _read_config()
    return cfg.get("exclude_issn", False)


def set_exclude_issn(enabled: bool) -> None:
    """Persist the exclude_issn setting."""
    cfg = _read_config()
    cfg["exclude_issn"] = enabled
    _write_config(cfg)


def get_exclude_doi() -> bool:
    """Return True if DOI should be excluded from BibTeX entries."""
    cfg = _read_config()
    return cfg.get("exclude_doi", False)


def set_exclude_doi(enabled: bool) -> None:
    """Persist the exclude_doi setting."""
    cfg = _read_config()
    cfg["exclude_doi"] = enabled
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
