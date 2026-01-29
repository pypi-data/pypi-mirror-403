# src/devopsmind/mentor/diagnostics.py

from devopsmind.state import load_state
from devopsmind.mentor.engine import mentor_healthcheck
from devopsmind.mentor.stagnation import detect_stagnation


def run_mentor_diagnostics(table):
    """
    Adds mentor-related diagnostics to the Doctor table.

    Rules:
    - NEVER prints
    - NEVER executes mentor advice
    - NEVER renders UI
    - SAFE for offline mode
    """

    state = load_state()
    mode = state.get("mode", "offline")

    # -------------------------------------------------
    # Mentor engine availability (SAFE health check)
    # -------------------------------------------------

    try:
        mentor_healthcheck()
        table.add_row(
            "Mentor system",
            "✅ Mentor engine live",
        )
    except Exception as e:
        table.add_row(
            "Mentor system",
            f"❌ Mentor unavailable ({type(e).__name__})",
        )
        return  # stop further mentor diagnostics safely

    # -------------------------------------------------
    # Execution mode
    # -------------------------------------------------

    if mode == "offline":
        table.add_row(
            "Offline mode",
            "ℹ️ Running in offline mode",
        )
    else:
        table.add_row(
            "Offline mode",
            "ℹ️ Running in online mode",
        )

    # -------------------------------------------------
    # User progress visibility
    # -------------------------------------------------

    completed = state.get("progress", {}).get("completed", [])
    table.add_row(
        "User progress",
        f"✅ {len(completed)} labs completed",
    )

    # -------------------------------------------------
    # Stagnation signal (read-only, safe)
    # -------------------------------------------------

    stagnation = detect_stagnation()
    if stagnation:
        table.add_row(
            "Stagnation detected",
            f"⚠️ Repeated failures on {stagnation['lab_id']}",
        )
    else:
        table.add_row(
            "Stagnation detected",
            "✅ No repeated failure patterns",
        )

    # -------------------------------------------------
    # Mentor provider (informational only)
    # -------------------------------------------------

    provider = "Rule-based"
    if state.get("ember_enabled"):
        provider = "Ember (local AI)"
    elif state.get("paid_entitlement"):
        provider = "Paid mentor"

    table.add_row(
        "Mentor provider",
        f"✅ {provider}",
    )
