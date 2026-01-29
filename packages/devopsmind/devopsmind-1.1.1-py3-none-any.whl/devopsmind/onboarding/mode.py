from rich.console import Console
from rich.text import Text

from devopsmind.onboarding.first_run import ensure_first_run
from devopsmind.state import load_state, save_state

console = Console()


def set_mode_online():
    """
    Enable online mode AFTER successful login.
    Only performs onboarding when transitioning from offline → online.
    """
    state = load_state()
    current = state.get("mode", "offline")

    # -------------------------------------------------
    # Already online → no duplicate output
    # -------------------------------------------------
    if current == "online":
        return Text("🌐 Already in online mode", style="dim")

    # -------------------------------------------------
    # Transition: offline → online
    # -------------------------------------------------
    ensure_first_run(force=True)

    # Reload state after first-run hydration
    state = load_state()

    state["mode"] = "online"
    state.setdefault("auth", {})
    state["auth"]["lock_enabled"] = True

    save_state(state)

    msg = Text("🌐 Online mode enabled", style="green")
    console.print(msg)
    return msg


def set_mode_offline():
    """
    Switch to offline mode (no authentication required).
    """
    state = load_state()
    current = state.get("mode", "offline")

    # -------------------------------------------------
    # Already offline → no duplicate output
    # -------------------------------------------------
    if current == "offline":
        return Text("📴 Already in offline mode", style="dim")

    # -------------------------------------------------
    # Transition: online → offline
    # -------------------------------------------------
    state["mode"] = "offline"
    state.setdefault("auth", {})
    state["auth"]["lock_enabled"] = False

    save_state(state)

    msg = Text("📴 Offline mode enabled", style="yellow")
    console.print(msg)
    return msg
