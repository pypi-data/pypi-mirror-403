# src/devopsmind/handlers/project/reset.py

"""
devopsmind project reset <project_id>

- Destructive reset (workspace + progress)
- Requires explicit confirmation
- Deletes project workspace
- Resets project state to not-started
- UX identical to lab reset
"""

from pathlib import Path
import shutil
import subprocess

from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm

from devopsmind.handlers.ui_helpers import boxed
from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.project.describe import _available_project_ids
from devopsmind.state import load_state, save_state

console = Console()

# -------------------------------------------------
# Paths
# -------------------------------------------------
WORKSPACE_ROOT = Path.home() / "workspace" / "project"


# -------------------------------------------------
# 🚀 PUBLIC ENTRYPOINT
# -------------------------------------------------
def handle_project_reset(args, console: Console = console):
    if not args.project_id:
        console.print(
            boxed(
                "❌ Reset Failed",
                Text("Project ID required.", style="red"),
            )
        )
        return

    project_id = canonical_id(args.project_id)
    workspace = WORKSPACE_ROOT / project_id

    # -------------------------------------------------
    # Validate project availability
    # -------------------------------------------------
    if project_id not in _available_project_ids():
        console.print(
            boxed(
                "❌ Reset Failed",
                Text(
                    f"Project '{project_id}' not found or not available.",
                    style="red",
                ),
            )
        )
        return

    # -------------------------------------------------
    # Nothing to reset
    # -------------------------------------------------
    if not workspace.exists():
        console.print(
            boxed(
                "ℹ Nothing to Reset",
                Text(
                    "No workspace exists for this project.\n\n"
                    "You can start it using:\n"
                    f"  devopsmind project start {project_id}",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # Destructive confirmation (MANDATORY)
    # -------------------------------------------------
    if not Confirm.ask(
        f"[red]Reset project '{project_id}'?[/red]\n"
        "This will permanently delete:\n"
        "- All project files\n"
        "- All written artifacts\n"
        "- Any local evidence\n\n"
        "This action cannot be undone."
    ):
        console.print(
            boxed(
                "Reset Cancelled",
                Text("No changes were made.", style="dim"),
            )
        )
        return

    # -------------------------------------------------
    # Kill any related containers (best effort)
    # -------------------------------------------------
    subprocess.run(
        ["docker", "rm", "-f", f"devopsmind-project-{project_id}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # -------------------------------------------------
    # HARD RESET: delete workspace entirely
    # -------------------------------------------------
    shutil.rmtree(workspace, ignore_errors=True)

    # -------------------------------------------------
    # Reset project state
    # -------------------------------------------------
    state = load_state() or {}
    projects = state.setdefault("projects", {})

    if project_id in projects:
        projects.pop(project_id)

    save_state(state)

    # -------------------------------------------------
    # ✅ Success UI
    # -------------------------------------------------
    console.print(
        boxed(
            "♻ Project Reset Complete",
            Text(
                f"'{project_id}' has been fully reset.\n\n"
                "The next start will be a clean, brand-new run:\n"
                f"  devopsmind project start {project_id}",
                style="green",
            ),
        )
    )
