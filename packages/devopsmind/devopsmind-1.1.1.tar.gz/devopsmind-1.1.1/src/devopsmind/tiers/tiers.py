from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from devopsmind.state import load_state
from devopsmind.license.license_manager import (
    load_license,
    core_pro_active,
    domain_active,
    domain_plus_active,
)

console = Console()


def _load_catalog() -> dict:
    path = Path(__file__).parent / "meta" / "tiers_catalog.yaml"
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _tier_status(tier: str, owned: set[str], license_data: dict) -> str:
    if tier in owned:
        if tier == "foundation_core":
            return "🟢 Owned"

        if tier == "core_pro" and core_pro_active(license_data):
            return "🟢 Owned"

        if tier.startswith("domain_plus_"):
            role = tier.removeprefix("domain_plus_")
            return "🟢 Owned" if domain_plus_active(license_data, role) else "🟡 Expired"

        if tier.startswith("domain_"):
            domain = tier.removeprefix("domain_")
            return "🟢 Owned" if domain_active(license_data, domain) else "🟡 Expired"

        return "🟡 Expired"

    return "🔒 Locked"


def show_tiers():
    state = load_state()
    owned = set(state.get("tiers", {}).get("owned", []))
    license_data = load_license()
    catalog = _load_catalog()

    blocks = []

    for tier, meta in catalog.items():
        status = _tier_status(tier, owned, license_data)

        body = [
            Text(meta.get("description", ""), style="dim"),
            Text(""),
        ]

        for item in meta.get("teaches", []):
            body.append(Text(f"• {item}"))

        body.append(Text(""))
        body.append(Text(f"Status: {status}", style="bold"))

        blocks.append(
            Panel(
                Text("\n").join(body),
                title=meta.get("title", tier),
                border_style="green" if "Owned" in status else "yellow",
            )
        )

    blocks.append(
        Panel(
            Text(
                "ℹ️ Use `devopsmind pricing` to view plans\n"
                "ℹ️ Use `devopsmind activate <tier>` to unlock",
                style="dim",
            ),
            title="Next Steps",
        )
    )

    for block in blocks:
        console.print(block)
