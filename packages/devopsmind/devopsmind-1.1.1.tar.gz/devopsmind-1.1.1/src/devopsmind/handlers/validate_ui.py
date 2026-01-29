from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
import os

from devopsmind.achievements import list_badges
from devopsmind.state import load_state


def _format_sync_status(sync_status):
    """
    Convert sync response into human-readable text.
    UI ONLY.
    """

    state = load_state()
    mode = state.get("mode", "offline")

    # 🔒 FORCE offline display
    if mode == "offline":
        return "📴 Offline (sync disabled)"

    # --- Online-only logic below ---

    if sync_status is None:
        return "🏆 Already synced"

    if isinstance(sync_status, str):
        return sync_status

    if isinstance(sync_status, dict):
        if sync_status.get("ok") is True:
            return "✅ Sync complete"
        if sync_status.get("pending") is True:
            return "⏳ Sync pending"
        if sync_status.get("already") is True:
            return "🏆 Already synced"
        if sync_status.get("error"):
            return "⚠️ Sync failed"

    return "—"


def show_validation_result(
    lab_id,
    stack=None,
    difficulty=None,
    skills=None,
    xp_awarded=None,
    xp_message=None,
    milestone_bonus=None,
    message=None,
    earned_badges=None,
    sync_status=None,
    mentor_after=None,
    solution=None,
):
    """
    Render validation result.
    """

    skills = skills or []
    earned_badges = earned_badges or []

    renderables = []

    table = Table(show_header=False, box=None, expand=True)
    table.add_column("Key", style="dim", width=14)
    table.add_column("Value", overflow="fold")

    table.add_row("Lab", lab_id)

    if stack:
        table.add_row("Stack", f"🛠️ {stack}")

    if difficulty:
        table.add_row("Difficulty", f"🎯 {difficulty}")

    if skills:
        table.add_row(
            "Skills",
            " · ".join(f"🔹 {s}" for s in skills),
        )

    if xp_message is None:
        parts = []
        if xp_awarded:
            parts.append(f"+{xp_awarded} effort")
        if milestone_bonus and milestone_bonus > 0:
            parts.append("🎯 Milestone achieved")
        if parts:
            xp_message = " · ".join(parts)

    if xp_message:
        table.add_row("Effort", f"🧩 {xp_message}")
    elif xp_awarded:
        table.add_row("Effort", f"🧩 +{xp_awarded}")

    table.add_row("Sync", _format_sync_status(sync_status))

    renderables.append(
        Panel(
            table,
            title="✅ Lab Validated",
            border_style="green",
        )
    )

    if earned_badges:
        text = Text()

        try:
            badges = list_badges(raw=True)
            badge_map = {b["id"]: b for b in badges}
        except Exception:
            badge_map = {}

        for badge_id in earned_badges:
            meta = badge_map.get(badge_id)
            if not meta:
                continue

            if meta.get("hidden") is True or meta.get("category") == "secret":
                continue

            text.append(f"{meta.get('icon','🏅')} {meta.get('name', badge_id)}\n")

        if text.plain.strip():
            renderables.append(
                Panel(
                    text,
                    title="🎉 New Achievements Unlocked",
                    border_style="yellow",
                )
            )

    if mentor_after:
        renderables.append(
            Panel(
                Text(mentor_after),
                title="🧭 Mentor Guidance",
                border_style="cyan",
            )
        )

    # -------------------------------------------------
    # 📘 Solution Walkthrough (UPDATED – NEW KEYS ONLY)
    # -------------------------------------------------
    if isinstance(solution, dict):
        blocks = []

        overview = solution.get("overview")
        if overview:
            blocks.append(Text("🎯 Overview\n", style="bold cyan"))
            blocks.append(Text(overview.strip() + "\n\n", style="cyan"))

        reasoning = solution.get("professional_reasoning")
        if isinstance(reasoning, list) and reasoning:
            blocks.append(Text("🧠 Professional Reasoning\n", style="bold cyan"))
            for r in reasoning:
                blocks.append(Text(f"• {r}\n", style="cyan"))
            blocks.append(Text("\n"))

        commands = solution.get("commands")
        if isinstance(commands, list) and commands:
            blocks.append(Text("🧪 Commands (Real-World Reference)\n", style="bold cyan"))
            for c in commands:
                if isinstance(c, dict):
                    cmd = c.get("cmd")
                    purpose = c.get("purpose")
                    if cmd:
                        blocks.append(Text(f"• {cmd}\n", style="cyan"))
                    if purpose:
                        blocks.append(Text(f"  → {purpose}\n", style="dim cyan"))
            blocks.append(Text("\n"))

        context = solution.get("real_world_context")
        if isinstance(context, list) and context:
            blocks.append(Text("🌍 Real-World Context\n", style="bold cyan"))
            for c in context:
                blocks.append(Text(f"• {c}\n", style="cyan"))

        if blocks:
            renderables.append(
                Panel(
                    Group(*blocks),
                    title="📘 Solution Walkthrough (Real-World)",
                    border_style="cyan",
                )
            )

    if os.environ.get("DEVOPSMIND_SAFE") != "1":
        renderables.append(
            Panel(
                Text(
                    "🧹 Workspace cleaned\n"
                    "👋 Returning to main shell",
                    style="magenta",
                ),
                title="⚙️ System",
                border_style="magenta",
            )
        )

    return Group(*renderables)


def show_secret_reveal(secret_achievements):
    """
    Reveal hidden achievements without spoilers.
    Shown ONLY when a secret is newly unlocked.
    """

    if not secret_achievements:
        return None

    lines = [
        "You unlocked a hidden achievement.",
        "",
    ]

    for ach in secret_achievements:
        lines.append(f"{ach.get('icon','🏅')} {ach.get('name')}")

    lines.append("")
    lines.append("(Some achievements are revealed only once)")

    return Panel(
        Text("\n".join(lines)),
        title="🎭 Something Changed",
        border_style="magenta",
    )
