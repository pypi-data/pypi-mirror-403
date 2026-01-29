# src/devopsmind/tiers/__init__.py

"""
Tier ownership package.

Holds local, user-owned entitlement data.
Offline-first and mentor-safe.
"""

from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()


def show_tiers():
    """
    Display locally owned tiers and labs.

    Backward-compatible public API.
    """

    tiers_dir = Path.home() / ".devopsmind" / "tiers"

    if not tiers_dir.exists():
        console.print(
            Panel(
                "No tiers found.\n\nYou are using the Free tier.",
                title="DevOpsMind Tiers",
                border_style="cyan",
            )
        )
        return

    lines = []

    for tier_file in sorted(tiers_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(tier_file.read_text()) or {}
        except Exception:
            continue

        tier_name = data.get("name", tier_file.stem)
        labs = data.get("labs", [])

        lines.append(f"[bold]{tier_name}[/bold]")
        for c in labs:
            lines.append(f"  • {c}")

        lines.append("")

    console.print(
        Panel(
            "\n".join(lines).rstrip(),
            title="DevOpsMind Tiers",
            border_style="cyan",
        )
    )
