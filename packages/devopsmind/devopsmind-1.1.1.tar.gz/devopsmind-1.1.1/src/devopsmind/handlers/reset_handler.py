from pathlib import Path
import shutil
import subprocess

from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm

from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.handlers.ui_helpers import boxed

WORKSPACE_ROOT = Path.home() / "workspace"
console = Console()


def handle_reset(args, console: Console = console):
    lab_id = args.id

    # -------------------------------------------------
    # Validate lab existence (source of truth)
    # -------------------------------------------------
    source = find_lab_by_id(lab_id)
    if not source:
        console.print(
            boxed(
                "❌ Reset Failed",
                Text(f"Lab '{lab_id}' not found.", style="red"),
            )
        )
        return

    workspace = WORKSPACE_ROOT / lab_id

    # -------------------------------------------------
    # Nothing to reset
    # -------------------------------------------------
    if not workspace.exists():
        console.print(
            boxed(
                "ℹ Nothing to Reset",
                Text(
                    "No workspace exists for this lab.\n\n"
                    "You can start it using:\n"
                    f"  devopsmind start {lab_id}",
                    style="yellow",
                ),
            )
        )
        return

    # -------------------------------------------------
    # Destructive confirmation (MANDATORY)
    # -------------------------------------------------
    if not Confirm.ask(
        f"[red]Reset lab '{lab_id}'?[/red]\n"
        "This will permanently delete:\n"
        "- All files\n"
        "- All git history & commits\n"
        "- All progress & secrets\n\n"
        "This action cannot be undone."
    ):
        return

    # -------------------------------------------------
    # Kill any related containers (best effort)
    # -------------------------------------------------
    subprocess.run(
        ["docker", "rm", "-f", f"devopsmind-{lab_id}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # -------------------------------------------------
    # HARD RESET: delete workspace entirely
    # -------------------------------------------------
    shutil.rmtree(workspace, ignore_errors=True)

    console.print(
        boxed(
            "♻ Lab Reset Complete",
            Text(
                f"'{lab_id}' has been fully reset.\n\n"
                "The next start will be a clean, brand-new run:\n"
                f"  devopsmind start {lab_id}",
                style="green",
            ),
        )
    )
