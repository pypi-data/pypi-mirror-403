from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def _load_pricing() -> dict:
    path = Path(__file__).parent / "meta" / "pricing_catalog.yaml"
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _render_simple_pricing(pricing: dict, body: list):
    for period, cost in pricing.items():
        india = cost.get("india", "—")
        global_ = cost.get("global", "—")
        body.append(Text(f"  {period} → {india} / {global_}"))


def _render_team_pricing(pricing: dict, body: list):
    for tier_name, tier_pricing in pricing.items():
        body.append(Text(f"{tier_name.replace('_', ' ').title()}:", style="bold"))
        for period, cost in tier_pricing.items():
            india = cost.get("india", "—")
            global_ = cost.get("global", "—")
            body.append(Text(f"  {period} → {india} / {global_}"))
        body.append(Text(""))


def show_pricing():
    pricing_data = _load_pricing()

    for key, item in pricing_data.items():
        body = []

        # -------------------------------------------------
        # Simple fixed price (Foundation)
        # -------------------------------------------------
        if "price" in item:
            body.append(Text(f"Price: {item['price']['india']} / {item['price']['global']}"))
            body.append(Text(f"Duration: {item.get('duration', '—')}"))
            body.append(Text(""))

        # -------------------------------------------------
        # Pricing blocks (individual / team)
        # -------------------------------------------------
        if "pricing" in item:
            body.append(Text("Pricing:", style="bold"))

            pricing = item["pricing"]

            # Detect nested pricing (team)
            if any(isinstance(v, dict) and "india" not in v for v in pricing.values()):
                _render_team_pricing(pricing, body)
            else:
                _render_simple_pricing(pricing, body)

            body.append(Text(""))

        # -------------------------------------------------
        # Includes
        # -------------------------------------------------
        if "includes" in item:
            body.append(Text("Includes:", style="bold"))
            for inc in item["includes"]:
                body.append(Text(f"• {inc}"))
            body.append(Text(""))

        # -------------------------------------------------
        # Notes
        # -------------------------------------------------
        if "note" in item:
            body.append(Text(item["note"], style="dim"))

        console.print(
            Panel(
                Text("\n").join(body),
                title=item.get("title", key),
                border_style="cyan",
            )
        )

    # -------------------------------------------------
    # Footer
    # -------------------------------------------------
    console.print(
        Panel(
            Text(
                "ℹ️ Activation examples:\n"
                "  devopsmind activate core-pro\n"
                "  devopsmind activate full-stack-proplus\n\n"
                "ℹ️ Use `devopsmind tiers` to see learning content",
                style="dim",
            ),
            title="Next Steps",
        )
    )

