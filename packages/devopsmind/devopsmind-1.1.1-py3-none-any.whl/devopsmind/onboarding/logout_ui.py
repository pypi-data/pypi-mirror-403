# devopsmind/logout_ui.py

from pathlib import Path
from rich.panel import Panel
from rich.text import Text

DEVOPSMIND_DIR = Path.home() / ".devopsmind"


def logout_warning_panel():
    return Panel(
        Text(
            "⚠️ You are about to log out from this machine.\n\n"
            "This will DELETE all local DevOpsMind data stored at:\n\n"
            f"  {DEVOPSMIND_DIR}\n\n"
            "Including:\n"
            "- progress (state.json)\n"
            "- XP & achievements\n"
            "- offline license copy (license.json)\n"
            "- owned tier markers (tiers/*.yaml)\n"
            "- restore snapshot (snapshot.json)\n\n"
            "Important:\n"
            "- Editing files inside ~/.devopsmind/ manually is NOT supported\n"
            "- Manual changes may corrupt progress, licenses, or restore data\n"
            "- Your license and owned content are NOT revoked by logout\n\n"
            "You may back up this directory before continuing.\n",
            style="yellow",
        ),
        title="Logout Warning",
        border_style="yellow",
    )
