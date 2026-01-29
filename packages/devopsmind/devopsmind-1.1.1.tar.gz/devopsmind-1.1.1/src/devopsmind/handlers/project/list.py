# src/devopsmind/handlers/project/list.py

"""
devopsmind projects

Lists AVAILABLE projects declared in tier YAMLs.

Rules:
- Read-only
- Tier YAMLs are the ONLY source of truth
- No ownership or progress semantics
- No state mutation
"""

from pathlib import Path
import yaml

from rich.table import Table
from rich.panel import Panel
from rich.console import Group
from rich.text import Text

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.state import load_state

# -------------------------------------------------
# Paths (LOCKED & CORRECT)
# -------------------------------------------------
TIERS_DIR = Path.home() / ".devopsmind" / "tiers"

# devopsmind/labs (correct anchor)
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


def _parse_tier_and_version(stem: str) -> tuple[str, int | None]:
    """
    domain_observability_v2 -> (domain_observability, 2)
    domain_security        -> (domain_security, None)
    """
    if "_v" in stem:
        base, _, v = stem.rpartition("_v")
        try:
            return base, int(v)
        except ValueError:
            return stem, None
    return stem, None


def _resolve_project_meta(project_id: str) -> dict | None:
    """
    Resolve project metadata using fixed layout:

    labs/<Domain>/Projects/<project_id>/project.yaml
    """
    for domain_dir in LABS_DIR.iterdir():
        if not domain_dir.is_dir():
            continue

        project_dir = domain_dir / "Projects" / project_id
        project_yaml = project_dir / "project.yaml"

        if not project_yaml.exists():
            continue

        meta = _load_yaml(project_yaml)

        return {
            "id": meta.get("id", project_id),
            "title": meta.get("title", project_id),
            "difficulty": meta.get("difficulty", "Unknown"),
            "xp": int(meta.get("xp", 0)),
        }

    return None


# -------------------------------------------------
# Command Handler
# -------------------------------------------------
def handle_projects(args):
    """
    devopsmind projects
    """

    panels = []

    if not TIERS_DIR.exists():
        return Panel(
            Text("No tiers found. Projects are unavailable.", style="dim"),
            border_style="blue",
        )

    # 🔒 AUTHORITATIVE OWNERSHIP (VERSION-AWARE)
    state = load_state() or {}
    owned = state.get("tiers", {}).get("owned", {})

    # Tier YAMLs are authoritative (filtered by ownership + version)
    for tier_file in sorted(TIERS_DIR.glob("*.yaml")):
        tier_name, tier_version = _parse_tier_and_version(tier_file.stem)

        meta = owned.get(tier_name)
        if not meta:
            continue  # tier not owned at all

        owned_version = meta.get("version")

        # If versioned, must match owned version
        if owned_version is not None and tier_version is not None:
            if tier_version != owned_version:
                continue

        tier = _load_yaml(tier_file)

        project_ids = [
            canonical_id(pid)
            for pid in tier.get("project_ids", [])
        ]

        if not project_ids:
            continue

        table = Table(
            show_header=True,
            header_style="bold cyan",
        )

        table.add_column("Project ID")
        table.add_column("Effort", justify="right")
        table.add_column("Difficulty")

        for pid in project_ids:
            meta = _resolve_project_meta(pid)
            if not meta:
                continue

            table.add_row(
                meta["id"],
                str(meta["xp"]),
                meta["difficulty"],
            )

        domain_name = tier.get(
            "name",
            tier_name.replace("_", " ").title(),
        )

        panels.append(
            Panel(
                table,
                title=f"📦 {domain_name} Projects",
                border_style="blue",
            )
        )

    if not panels:
        return Panel(
            Text("No projects available", style="dim"),
            border_style="blue",
        )

    panels.append(
        Panel(
            Text(
                "Use `devopsmind project start <project_id>` to start\n"
                "Use `devopsmind project status <project_id>` to view project details",
                style="dim",
            ),
            border_style="blue",
        )
    )

    return Group(*panels)
