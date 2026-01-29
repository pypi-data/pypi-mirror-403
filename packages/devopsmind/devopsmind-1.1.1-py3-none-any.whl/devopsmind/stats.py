from pathlib import Path
import json

from rich.table import Table
from rich.panel import Panel

from .progress import load_state
from .constants import XP_LEVELS
from devopsmind.handlers.xp_bar import compute_rank_progress

SNAPSHOT_PATH = Path.home() / ".devopsmind" / "snapshot.json"


def _load_snapshot():
    if not SNAPSHOT_PATH.exists():
        return {}

    try:
        return json.loads(SNAPSHOT_PATH.read_text())
    except Exception:
        return {}


def stats():
    """
    Unified stats for CLI display.

    LOCKED RULES:
    - XP is AUTHORITATIVE from state
    - Rank is derived from LAB XP only
    - Stats are READ-ONLY (no mutation)
    - Snapshot is identity-only
    """

    state = load_state()
    snapshot = _load_snapshot()

    progress = state.get("progress", {})
    profile = state.get("profile", {})
    xp_data = state.get("xp", {})

    # -----------------------------
    # XP & Rank (AUTHORITATIVE)
    # -----------------------------
    xp_info = compute_rank_progress(xp_data)

    # -----------------------------
    # Identity (snapshot wins)
    # -----------------------------
    username = profile.get("username", "-")
    gamer = profile.get("gamer", "-")

    if snapshot:
        username = snapshot.get("username", username)
        gamer = snapshot.get("handle", gamer)

    # -----------------------------
    # 🎨 RENDER
    # -----------------------------
    table = Table(show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value", overflow="fold")

    table.add_row("User", username)
    table.add_row("Handle", gamer)
    table.add_row("Role", xp_info["current_rank"])
    table.add_row("Effort", xp_info["effort_fmt"])
    table.add_row("Completed Labs", str(len(progress.get("completed", []))))
    table.add_row("Badges", str(len(state.get("badges", []))))
    table.add_row("Streak Days", str(state.get("streak_days", 0)))
    table.add_row("Mode", state.get("mode", "offline"))

    # -----------------------------
    # 🧭 Projects (CONDITIONAL)
    # -----------------------------
    projects = state.get("projects", {})

    if projects:
        started = len(projects)
        completed = sum(1 for v in projects.values() if v == "completed")

        table.add_row("Projects Started", str(started))
        table.add_row("Projects Completed", str(completed))

    return Panel(
        table,
        title="📊 DevOpsMind Stats",
        border_style="cyan",
    )
