"""
DevOpsMind Runtime Context

This module is imported extremely early (via autocomplete hook).
It must be:
- Fast (no heavy imports)
- Deterministic
- Side-effect free
- Future-proof

Purpose:
- Detect command intent
- Classify execution path
- Enable fast paths without touching main.py
"""

import sys
import os

# -------------------------------------------------
# Raw command detection
# -------------------------------------------------

RAW_CMD = sys.argv[1] if len(sys.argv) > 1 else ""

# -------------------------------------------------
# Execution classes
# -------------------------------------------------

# Internal / system commands (autocomplete, helpers)
IS_INTERNAL = RAW_CMD.startswith("__")

# Help / version flags
IS_HELP = RAW_CMD in ("--help", "--version")

# Login is special (bootstrap required)
IS_LOGIN = RAW_CMD == "login"

# Lightweight user commands (read-only, fast)
IS_LIGHT = RAW_CMD in (
    "stats",
    "badges",
    "profile",
    "leaderboard",
)

# Everything else is heavy by default
IS_HEAVY = not (
    IS_INTERNAL
    or IS_HELP
    or IS_LOGIN
    or IS_LIGHT
)

# -------------------------------------------------
# Fast mode (opt-in)
# -------------------------------------------------

# Power users / CI / completion can force fast startup
FAST_MODE = os.environ.get("DEVOPSMIND_FAST") == "1"

# -------------------------------------------------
# Derived intent flags (future use)
# -------------------------------------------------

# Commands that mutate state
IS_MUTATING = RAW_CMD in (
    "start",
    "validate",
    "submit",
    "sync",
    "mentor",
)


# -------------------------------------------------
# Debug / introspection helpers
# -------------------------------------------------

def runtime_summary() -> dict:
    """
    Returns runtime classification.
    Safe for debug / doctor commands.
    """
    return {
        "raw_cmd": RAW_CMD,
        "is_internal": IS_INTERNAL,
        "is_help": IS_HELP,
        "is_login": IS_LOGIN,
        "is_light": IS_LIGHT,
        "is_heavy": IS_HEAVY,
        "fast_mode": FAST_MODE,
        "is_mutating": IS_MUTATING,
        "is_ui": IS_UI,
    }
