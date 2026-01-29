from pathlib import Path
import yaml
from rich.panel import Panel
from rich.console import Console

console = Console()

def load_lab_metadata(lab_dir: Path) -> dict:
    yaml_path = lab_dir / "lab.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError("lab.yaml not found")

    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def print_lab_header(
    meta: dict,
    action: str,
    icon: str,
    border_style: str
):
    title = meta.get("title", meta.get("id", "Unknown Lab"))

    console.print(
        Panel.fit(
            f"{icon} {action}\n\n[bold]{title}[/bold]",
            border_style=border_style
        )
    )
