# src/devopsmind/handlers/project/describe.py

"""
devopsmind project describe <project_id>

Renders the project description.
- Read-only
- No state mutation
- No ownership semantics
- Project must be declared in tier YAMLs
"""

from pathlib import Path
import yaml

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from devopsmind.handlers.id_normalizer import canonical_id

# -------------------------------------------------
# Paths (LOCKED)
# -------------------------------------------------
TIERS_DIR = Path.home() / ".devopsmind" / "tiers"
DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _available_project_ids() -> set[str]:
    """
    Collect ALL available project IDs from tier YAMLs.
    Tier YAMLs are the only source of truth.
    """
    ids = set()

    for tier_file in TIERS_DIR.glob("*.yaml"):
        tier = _load_yaml(tier_file)
        for pid in tier.get("project_ids", []):
            ids.add(canonical_id(pid))

    return ids


def _resolve_description(project_id: str) -> Path | None:
    """
    Resolve description.md using fixed layout:

    labs/<Domain>/Projects/<project_id>/description.md
    """
    for domain_dir in LABS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue

        desc = (
            domain_dir
            / "Projects"
            / project_id
            / "description.md"
        )

        if desc.exists():
            return desc

    return None


# -------------------------------------------------
# Command Handler
# -------------------------------------------------
def handle_project_describe(args):
    """
    devopsmind project describe <project_id>
    """

    if not args.project_id:
        return Panel(
            Text("Project ID is required", style="red"),
            border_style="red",
        )

    project_id = canonical_id(args.project_id)

    # -------------------------------------------------
    # Availability gate (MANDATORY)
    # -------------------------------------------------
    available = _available_project_ids()
    if project_id not in available:
        return Panel(
            Text(f"Project '{project_id}' is not available", style="red"),
            border_style="red",
        )

    # -------------------------------------------------
    # Resolve description.md
    # -------------------------------------------------
    desc_path = _resolve_description(project_id)
    if not desc_path:
        return Panel(
            Text("description.md not found for this project", style="red"),
            border_style="red",
        )

    try:
        content = desc_path.read_text()
    except Exception:
        return Panel(
            Text("Failed to read description.md", style="red"),
            border_style="red",
        )

    # -------------------------------------------------
    # Render (READ-ONLY UX)
    # -------------------------------------------------
    return Panel(
        Markdown(content),
        border_style="blue",
    )
