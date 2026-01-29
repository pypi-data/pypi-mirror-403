"""
Streak management for DevOpsMind.

A streak represents consecutive days with at least one
successful learning action (e.g. validation success).

Design rules:
- Updated ONLY on success
- Never updated on app launch
- Offline-safe (local date only)
- Idempotent (safe to call multiple times per day)
- One-time notification on streak break
"""

from datetime import date, timedelta
from devopsmind.state import load_state, save_state


# -------------------------------------------------
# Core streak update (WRITE)
# -------------------------------------------------

def update_streak_on_success():
    """
    Update streak counters after a successful learning action.

    This function is safe to call multiple times per day.
    It will:
    - increment streak if consecutive day
    - reset streak if a day was missed
    - mark streak break for notification (once)
    """
    state = load_state()

    today = date.today()
    today_str = today.isoformat()

    last_date_str = state.get("last_active_date")
    streak = state.get("streak_days", 0)

    streak_broken = False

    if last_date_str:
        try:
            last_date = date.fromisoformat(last_date_str)
        except ValueError:
            # Corrupt date → reset safely
            last_date = None

        if last_date == today:
            # Already counted today → no-op
            return

        if last_date == today - timedelta(days=1):
            # Consecutive day
            streak += 1
        else:
            # Streak broken
            streak = 1
            streak_broken = True
    else:
        # First ever successful activity
        streak = 1

    state["streak_days"] = streak
    state["last_active_date"] = today_str

    if streak_broken:
        state["streak_broken_on"] = (today - timedelta(days=1)).isoformat()
        state["streak_notified"] = False

    save_state(state)


# -------------------------------------------------
# Read-only helpers (UI / stats)
# -------------------------------------------------

def get_streak_state():
    """
    Read-only helper for UI or stats.
    Always returns safe defaults.
    """
    state = load_state()

    return {
        "streak_days": state.get("streak_days", 0),
        "last_active_date": state.get("last_active_date"),
    }


def get_streak_notification():
    """
    Returns the date when the streak was broken
    if the user has not yet been notified.

    Returns:
        str (YYYY-MM-DD) or None
    """
    state = load_state()

    if state.get("streak_notified"):
        return None

    broken_on = state.get("streak_broken_on")
    if not broken_on:
        return None

    return broken_on


# -------------------------------------------------
# Notification control
# -------------------------------------------------

def mark_streak_notified():
    """
    Mark streak break notification as shown.
    Ensures the user is notified only once per break.
    """
    state = load_state()
    state["streak_notified"] = True
    save_state(state)

