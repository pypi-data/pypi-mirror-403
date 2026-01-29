# src/devopsmind/programs/lifecycle.py

"""
Program lifecycle resolution.

Responsibilities:
- Determine visibility of programs
- Handle grace period after expiry
- Expose future programs ("Coming soon")
- Provide a single source of truth for CLI filtering

This module is PURE logic.
NO UI. NO Rich. NO printing.
"""

from datetime import date, timedelta
from typing import Literal

from devopsmind.programs.policy_loader import load_policy


# --------------------------------------------------
# Constants (AUTHORITATIVE)
# --------------------------------------------------

# How long an expired program remains visible (read-only)
EXPIRED_GRACE_DAYS = 30


# --------------------------------------------------
# Lifecycle states (internal)
# --------------------------------------------------

LifecycleState = Literal[
    "ACTIVE",
    "UPCOMING",
    "GRACE",
    "HIDDEN",
]


# --------------------------------------------------
# Core lifecycle resolver
# --------------------------------------------------

def resolve_program_lifecycle(program: str) -> LifecycleState:
    """
    Determines lifecycle state for a program.

    Returns:
      ACTIVE   → usable, enterable
      UPCOMING → visible, not usable (future)
      GRACE    → visible, expired but still shown
      HIDDEN   → completely removed from UI
    """

    policy = load_policy(program)
    if not policy or "window" not in policy:
        # Dev / internal programs fail-open
        return "ACTIVE"

    window = policy["window"]

    start = _parse_date(window["start"])
    end = _parse_date(window["end"])
    today = date.today()

    if today < start:
        return "UPCOMING"

    if start <= today <= end:
        return "ACTIVE"

    # Expired
    grace_end = end + timedelta(days=EXPIRED_GRACE_DAYS)
    if today <= grace_end:
        return "GRACE"

    return "HIDDEN"


# --------------------------------------------------
# Public helpers
# --------------------------------------------------

def is_program_visible(program: str) -> bool:
    """
    Whether program should appear in:
    - `devopsmind programs`
    - dashboards
    """
    return resolve_program_lifecycle(program) != "HIDDEN"


def is_program_executable(program: str) -> bool:
    """
    Whether program can be entered / run.
    """
    return resolve_program_lifecycle(program) == "ACTIVE"


def is_program_upcoming(program: str) -> bool:
    return resolve_program_lifecycle(program) == "UPCOMING"


def is_program_in_grace(program: str) -> bool:
    return resolve_program_lifecycle(program) == "GRACE"


def get_program_launch_month(program: str) -> str | None:
    """
    Returns a friendly launch hint like:
      'October 2026'

    Only valid for UPCOMING programs.
    """
    policy = load_policy(program)
    if not policy or "window" not in policy:
        return None

    start = _parse_date(policy["window"]["start"])
    return start.strftime("%B %Y")


def days_until_launch(program: str) -> int | None:
    """
    Returns number of days until program launch.

    Only valid for UPCOMING programs.
    """
    policy = load_policy(program)
    if not policy or "window" not in policy:
        return None

    start = _parse_date(policy["window"]["start"])
    today = date.today()

    if today >= start:
        return None

    return (start - today).days


def days_until_expiry(program: str) -> int | None:
    """
    Returns number of days until program ends.

    Only valid for ACTIVE programs.
    """
    policy = load_policy(program)
    if not policy or "window" not in policy:
        return None

    end = _parse_date(policy["window"]["end"])
    today = date.today()

    if today > end:
        return None

    return (end - today).days


# --------------------------------------------------
# Internals
# --------------------------------------------------

def _parse_date(value: str) -> date:
    from datetime import datetime

    try:
        return date.fromisoformat(value)
    except ValueError:
        return datetime.fromisoformat(value).date()
