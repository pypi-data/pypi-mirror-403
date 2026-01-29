"""
DevOpsMind Runtime Cache

Purpose:
- Cache slow-to-compute metadata
- Used by autocomplete & internal commands
- Zero side effects on import
"""

import json
from pathlib import Path
from typing import List, Dict
from .runtime import FAST_MODE

CACHE_DIR = Path.home() / ".devopsmind" / "cache"
CACHE_FILE = CACHE_DIR / "runtime.json"

CACHE_VERSION = 1


# -------------------------------------------------
# Internal helpers
# -------------------------------------------------

def _ensure_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> Dict:
    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r") as f:
            data = json.load(f)
        if data.get("version") != CACHE_VERSION:
            return {}
        return data
    except Exception:
        return {}


def _save(data: Dict):
    _ensure_dir()
    try:
        with CACHE_FILE.open("w") as f:
            json.dump(data, f)
    except Exception:
        pass


# -------------------------------------------------
# Public cache API
# -------------------------------------------------

def get_cached_commands() -> List[str] | None:
    if FAST_MODE:
        return None
    return _load().get("commands")


def set_cached_commands(commands: List[str]):
    data = _load()
    data.update({
        "version": CACHE_VERSION,
        "commands": commands,
    })
    _save(data)


def get_cached_labs() -> List[str] | None:
    if FAST_MODE:
        return None
    return _load().get("labs")


def set_cached_labs(labs: List[str]):
    data = _load()
    data.update({
        "version": CACHE_VERSION,
        "labs": labs,
    })
    _save(data)


def get_cached_stacks() -> List[str] | None:
    if FAST_MODE:
        return None
    return _load().get("stacks")


def set_cached_stacks(stacks: List[str]):
    data = _load()
    data.update({
        "version": CACHE_VERSION,
        "stacks": stacks,
    })
    _save(data)


def invalidate_cache():
    if CACHE_FILE.exists():
        try:
            CACHE_FILE.unlink()
        except Exception:
            pass
