# src/devopsmind/handlers/project/status.py

"""
devopsmind project status <project_id>

Read-only project status view.

- Shows lifecycle state
- Shows workspace presence
- Shows artifact completion
- Shows next valid command
"""

from pathlib import Path
import yaml

from rich.panel import Panel
from rich.console import Group
from rich.text import Text
from rich.table import Table

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.project.describe import _available_project_ids
from devopsmind.state import load_state

# -------------------------------------------------
# Paths (LOCKED)
# -------------------------------------------------
DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"
WORKSPACE_DIR = Path.home() / "workspace" / "project"


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _resolve_project_dir(project_id: str) -> Path | None:
    for domain in LABS_DIR.iterdir():
        p = domain / "Projects" / project_id
        if p.exists():
            return p
    return None


# -------------------------------------------------
# Command Handler
# -------------------------------------------------
def handle_project_status(args):
    if not args.project_id:
        return Panel(Text("Project ID required", style="red"), border_style="red")

    project_id = canonical_id(args.project_id)

    # Availability gate
    if project_id not in _available_project_ids():
        return Panel(
            Text(f"Project '{project_id}' is not available", style="red"),
            border_style="red",
        )

    state = load_state()
    project_state = state.get("projects", {}).get(project_id, "not-started")

    workspace = WORKSPACE_DIR / project_id
    workspace_exists = workspace.exists()

    project_dir = _resolve_project_dir(project_id)
    meta = _load_yaml(project_dir / "project.yaml") if project_dir else {}
    required = meta.get("artifacts", {}).get("required", [])
    xp = int(meta.get("xp", 0))

    # -------------------------------------------------
    # Artifact table
    # -------------------------------------------------
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Artifact")
    table.add_column("Status")

    for a in required:
        exists = workspace_exists and (workspace / a).exists()
        table.add_row(
            a,
            "✅ Present" if exists else "❌ Missing",
        )

    # -------------------------------------------------
    # Status summary panel
    # -------------------------------------------------
    summary = Panel(
        Text(
            f"State: {project_state}\n"
            f"Workspace: {'Present' if workspace_exists else 'Not created'}\n"
            f"Required Artifacts: {len(required)}\n"
            f"XP Value: {xp}",
        ),
        title="📊 Project Status",
        border_style="blue",
    )

    # -------------------------------------------------
    # Next action hint (state-aware)
    # -------------------------------------------------
    if project_state == "not-started":
        next_hint = f"Start the project:\n  devopsmind project start {project_id}"

    elif project_state == "in-progress":
        next_hint = (
            "Continue working on artifacts.\n\n"
            f"Validate when ready:\n  devopsmind project validate {project_id}"
        )

    elif project_state == "validated":
        next_hint = (
            "Project is validated.\n\n"
            f"Submit to finalize:\n  devopsmind project submit {project_id}\n\n"
            "⚠️ Submission is final."
        )

    else:  # completed
        next_hint = (
            "Project is complete.\n\n"
            "Explore other projects:\n"
            "  devopsmind projects"
        )

    hint_panel = Panel(
        Text(next_hint, style="dim"),
        border_style="blue",
    )

    return Group(
        summary,
        table,
        hint_panel,
    )
