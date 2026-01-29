from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import getpass

console = Console()


def activate_license(tier: str) -> None:
    """
    Activate an INDIVIDUAL license.

    PRE-LAUNCH BEHAVIOR:
    - Ask for license key
    - Validate format (basic)
    - Do NOT modify tiers or state
    - Explain what activation will do when live

    POST-LAUNCH:
    - Verify via Worker (D1)
    - Install tier YAML
    - Persist license.json
    """

    console.print(
        Panel(
            Text(
                f"Activation requested for:\n\n{tier}\n\n"
                "This is an individual license activation.",
                justify="center",
            ),
            title="🔐 License Activation",
            border_style="cyan",
        )
    )

    license_key = getpass.getpass("Enter license key: ").strip()

    if not license_key:
        console.print("❌ Activation cancelled.", style="red")
        return

    # Placeholder validation (format only)
    if len(license_key) < 10:
        console.print(
            Panel(
                Text("❌ Invalid license key format."),
                border_style="red",
            )
        )
        return

    console.print(
        Panel(
            Text(
                "License verification is not enabled yet.\n\n"
                "When paid launch is live, this will:\n"
                "• Verify license with DevOpsMind servers\n"
                "• Bind license to your email\n"
                "• Unlock selected tiers locally\n\n"
                "No changes were made.",
                justify="center",
            ),
            title="ℹ️ Not Active Yet",
            border_style="yellow",
        )
    )
