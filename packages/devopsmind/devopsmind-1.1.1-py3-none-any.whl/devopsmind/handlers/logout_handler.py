# devopsmind/handlers/logout_handler.py

import shutil
from pathlib import Path
from rich.panel import Panel
from rich.text import Text


def confirm_and_purge_local_state(console, logout_warning_panel):
    """
    Warn user and delete ~/.devopsmind across OSes.
    """

    devopsmind_dir = Path.home() / ".devopsmind"

    if not devopsmind_dir.exists():
        return True

    console.print(logout_warning_panel())

    answer = input("Continue? [y/N]: ").strip().lower()
    if answer != "y":
        console.print("❌ Logout cancelled.", style="dim")
        return False

    try:
        shutil.rmtree(devopsmind_dir)
        console.print("🗑️ Local DevOpsMind data removed.", style="green")
        return True
    except Exception as e:
        console.print(
            Panel(
                Text(f"Failed to delete {devopsmind_dir}\n\n{e}", style="red"),
                title="Logout Error",
                border_style="red",
            )
        )
        return False
