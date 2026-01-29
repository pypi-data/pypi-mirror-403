from rich.console import Group
from rich.text import Text

from devopsmind.constants import VERSION
from devopsmind.state import load_state
from devopsmind.cli.cli import frame
from devopsmind.handlers.xp_bar import compute_rank_progress


def welcome_screen():
    return Group(
        Text(f"DevOpsMind v{VERSION}", style="bold green"),
        Text(""),
        Text("Get started:", style="bold"),
        Text("• introduce        → optionally introduce yourself"),
        Text("• mentor           → guided next-step suggestions"),
        Text("• start <id>        → start a lab"),
        Text("• search <term>    → find labs"),
        Text("• stacks           → view stack progress"),
        Text("• profile show     → view your profile"),
        Text("• stats            → view progress summary"),
        Text("• doctor           → diagnose setup issues"),
        Text(""),
        Text("Tip: DevOpsMind works fully offline by default.", style="dim"),
        Text(
            "ℹ️  DevOpsMind stores local data in ~/.devopsmind — manual edits are not supported.",
            style="dim",
        ),
    )


def profile_bar():
    """
    Profile bar is STATE-BASED.
    It must NEVER call stats() or any UI renderer.
    """
    state = load_state()

    profile = state.get("profile", {})
    xp_data = state.get("xp", 0)
    streak = state.get("streak_days", 0)

    mode = state.get("mode", "offline")
    mode_label = "🌐 ONLINE" if mode == "online" else "📴 OFFLINE"
    mode_style = "green" if mode == "online" else "dim"

    # ---------------- Progress Bar (delegated) ----------------
    xp_info = compute_rank_progress(xp_data, bar_width=10)

    filled_char = "▰"
    empty_char = "▱"

    bar = (
        f"["
        f"[grey50]{filled_char * xp_info['filled']}[/grey50]"
        f"[dim]{empty_char * xp_info['empty']}[/dim]"
        f"]"
    )

    # ---------------- Progress Text ----------------
    if xp_info["next_rank"]:
        progress_part = (
            f"🏅 Role: {xp_info['current_rank']} · "
            f"⚙️ Role Progress {xp_info['percent']}% {bar} · "
            f"🧩 Effort Score {xp_info['effort_fmt']}"
        )
    else:
        progress_part = (
            f"🏅 Role: {xp_info['current_rank']} · "
            f"⚙️ Role Progress MAX {bar} · "
            f"🧩 Effort Score {xp_info['effort_fmt']}"
        )

    streak_part = f"🔥 {streak}d · " if streak > 0 else ""

    text = (
        f"🧭 {profile.get('gamer', '—')} · "
        f"{streak_part}"
        f"{progress_part} · "
        f"{mode_label}"
    )

    t = Text.from_markup(text, style=mode_style)
    t.no_wrap = True
    return t


def boxed(title: str, body):
    """
    Universal boxed layout.

    - Profile bar ALWAYS comes from state
    - Body can be any Rich renderable
    """
    items = [
        profile_bar(),
        Text(""),
        body,
    ]
    return frame(title, Group(*items))
