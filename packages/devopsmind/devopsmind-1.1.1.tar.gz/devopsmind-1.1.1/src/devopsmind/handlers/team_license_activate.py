from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import getpass

console = Console()


def team_activate(tier: str) -> None:
    """
    Activate a TEAM license.

    PRE-LAUNCH:
    - Accept license key
    - Explain behavior
    - No mutation

    POST-LAUNCH:
    - Verify via Worker (D1)
    - Bind first email
    - Create team license.json
    """

    console.print(
        Panel(
            Text(
                f"Team activation requested for:\n\n{tier}\n\n"
                "Team licensing is not live yet.",
                justify="center",
            ),
            title="👥 Team Activation",
            border_style="yellow",
        )
    )

    key = getpass.getpass("Enter TEAM license key: ").strip()

    if not key:
        console.print("❌ Activation cancelled.", style="red")
        return

    console.print(
        Panel(
            Text(
                "Team license verification is not enabled yet.\n\n"
                "No changes were made.\n"
                "Foundation Core remains active.",
                justify="center",
            ),
            title="ℹ️ Not Active Yet",
            border_style="cyan",
        )
    )


def team_status() -> None:
    console.print(
        Panel(
            Text(
                "Team licensing is not active yet.\n\n"
                "This command will show:\n"
                "• Activated tier\n"
                "• Bound emails\n"
                "• Seat usage (max 6)\n"
                "• Expiry",
                justify="center",
            ),
            title="👥 Team Status",
            border_style="yellow",
        )
    )


def team_add(email: str) -> None:
    console.print(
        Panel(
            Text(
                f"Requested to add team member:\n\n{email}\n\n"
                "Team management is not active yet.\n\n"
                "Rules (when live):\n"
                "• Max 6 users\n"
                "• Emails cannot be removed\n"
                "• Each user activates on their own machine",
                justify="center",
            ),
            title="👥 Add Team Member",
            border_style="yellow",
        )
    )
