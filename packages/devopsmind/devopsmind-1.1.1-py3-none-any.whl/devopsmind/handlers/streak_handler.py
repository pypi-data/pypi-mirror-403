from rich.panel import Panel
from rich.text import Text

from devopsmind.streak import (
    get_streak_notification,
    mark_streak_notified,
)


def handle_streak_notification(console):
    """
    Show streak break notification once, if applicable.
    Returns True if a notification was shown.
    """
    broken_on = get_streak_notification()

    if not broken_on:
        return False

    console.print(
        Panel(
            Text(
                f"🔥 Your learning streak was broken on {broken_on}.\n\n"
                "No worries — complete a lab today to start a new streak.",
                style="yellow",
            ),
            title="Streak Update",
            border_style="yellow",
        )
    )

    mark_streak_notified()
    return True
