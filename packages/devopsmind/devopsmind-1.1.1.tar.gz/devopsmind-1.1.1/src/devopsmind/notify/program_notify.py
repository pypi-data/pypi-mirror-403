from datetime import datetime, timezone
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

from devopsmind.state import load_state, save_state

console = Console()

BUILDTRACK_LAUNCH = datetime(2026, 2, 14, tzinfo=timezone.utc)


def maybe_notify_program_launch():
    state = load_state()
    now = datetime.now(timezone.utc)

    # ⛔ Not launched yet
    if now < BUILDTRACK_LAUNCH:
        return

    seen = state.setdefault("program_announcements_seen", [])

    # ⛔ Already shown
    if "buildtrack" in seen:
        return

    console.print(
        Panel(
            Text(
                "🎉 New Program Available: BuildTrack\n\n"
                "A guided DevOps program focused on execution,\n"
                "resilience, and delivery.\n\n"
                "Run:\n"
                "  devopsmind program buildtrack",
                style="bold",
            ),
            title="What's New",
            border_style="cyan",
        )
    )

    seen.append("buildtrack")
    state["program_announcements_seen"] = seen
    save_state(state)
