from rich.text import Text
from rich.panel import Panel

from .tier_loader import list_owned_tiers


def show_license_status():
    tiers = list_owned_tiers()

    lines = []
    lines.append("License Status")
    lines.append("──────────────")

    for tier in tiers:
        label = tier.replace("_", " ").title()
        lines.append(f"✔ {label}")

    lines.append("")
    lines.append("Owned tiers are permanent.")
    lines.append("License expiry affects only new installations.")

    return Panel(
        Text("\n".join(lines)),
        title="🔐 License",
        border_style="green",
    )
