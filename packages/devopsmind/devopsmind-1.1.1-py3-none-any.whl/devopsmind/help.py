from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime, date

from devopsmind.tiers.tier_loader import (
    user_has_projects,
    list_owned_stack_domains,
)

console = Console()


def show_help():
    help_text = (
        "DevOpsMind — Offline-first DevOps learning CLI\n\n"
        "Usage:\n"
        "  devopsmind <command> [options]\n\n"
        "Getting started:\n"
        "  init                  Initialize DevOpsMind runtime and defaults\n"
        "  login                 Onboard in offline or online mode (explicit)\n"
        "  logout                Delete ALL local DevOpsMind data (destructive)\n"
        "  introduce             Optionally introduce yourself to the community\n\n"
        "Core lab commands:\n"
        "  stacks                View labs and stack progress\n"
    )

    # -------------------------------------------------
    # Stack domains — fully data-driven
    # -------------------------------------------------
    domains = list_owned_stack_domains()

    for flag, display_name in sorted(domains.items()):
        help_text += f"    --{flag:<18} {display_name}\n"

    help_text += (
        "\n"
        "  start <id>             Start a lab (fresh workspace)\n"
        "  resume <id>            Resume an existing lab (no file changes)\n"
        "  reset <id>             Reset current lab workspace\n"
        "  validate <id>          Validate your lab solution\n"
        "  search <term>          Search labs\n"
        "  describe <id>          View lab details\n"
        "  hint <id>              Get a hint\n"
        "  mentor                 Guided next-step suggestions\n\n"
    )

    # -------------------------------------------------
    # Projects (capstone missions)
    # -------------------------------------------------
    if user_has_projects():
        help_text += (
            "Projects (capstone missions):\n"
            "  projects               List available projects\n"
            "  project describe <id>  View project briefing\n"
            "  project start <id>     Start a project (creates workspace)\n"
            "  project resume <id>    Resume an in-progress project\n"
            "  project status <id>    View project state and artifact status\n"
            "  project validate <id>  Validate required project artifacts\n"
            "  project submit <id>    Finalize project and earn XP (irreversible)\n\n"
        )

    # -------------------------------------------------
    # Programs (time-bound rollout window)
    # -------------------------------------------------
    today = date.today()
    program_start = date(2026, 2, 12)
    program_end = date(2026, 2, 28)

    if program_start <= today <= program_end:
        help_text += (
            "Programs (guided learning tracks):\n"
            "  programs               List available programs\n"
            "  program <name>         Open program dashboard or environment\n"
            "  program validate <p>   Validate program workspace\n"
            "  program simulate <p>   View learning objectives\n"
            "  program submit <p>     Complete program and earn certificate\n"
            "  program cert <p>       View program certificate\n\n"
        )

    help_text += (
        "Progress & profile:\n"
        "  stats                  View XP and progress summary\n"
        "  profile show           View your profile\n"
        "  badges                 View earned badges\n\n"
        "Utilities:\n"
        "  doctor                 Diagnose setup issues\n"
        "  sync                   Sync progress and leaderboard data\n"
        "  submit                 Submit completed labs\n"
        "  auth                   Recovery key rotation\n\n"
        "Modes:\n"
        "  mode online            Enable online mode\n"
        "  mode offline           Switch back to offline mode\n\n"
        "Other:\n"
        "  --version              Show version\n"
        "  --help                 Show this help\n\n"
        "Privacy & data:\n"
        "  • DevOpsMind works fully offline by default.\n"
        "  • `introduce` is optional and never automatic.\n"
        "  • `logout` permanently deletes local progress and identity.\n"
    )

    console.print(
        Panel(
            Text(help_text, style="white"),
            title="Help",
            border_style="cyan",
        )
    )
