import argparse
import sys
import shutil
from pathlib import Path
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.console import Group
from rich.progress import BarColumn
from rich.table import Table

from devopsmind.onboarding.first_run import ensure_first_run
from devopsmind.state import load_state, reset_session
from devopsmind.onboarding.mode import set_mode_online, set_mode_offline

from devopsmind.cli.cli import frame
from devopsmind.engine.engine import start, validate_only, stats as render_stats
from devopsmind.list.list import list_labs, search_labs
from devopsmind.profiles import show_profile, list_profiles
from devopsmind.engine.hint import show_hint
from devopsmind.engine.describe import describe_lab
from devopsmind.doctor import run_doctor
from devopsmind.restore.sync import sync_default
from devopsmind.submit import submit_pending
from devopsmind.constants import XP_LEVELS, VERSION
from devopsmind.list.stacks import show_my_stack_progress
from devopsmind.handlers.validate_ui import show_validation_result
from devopsmind.stats import stats as load_stats
from devopsmind.achievements import list_badges
from devopsmind.onboarding.introduce import run_introduce
from devopsmind.notify.update_notify import maybe_notify_update
from devopsmind.notify.program_notify import maybe_notify_program_launch
from devopsmind.onboarding.logout_ui import logout_warning_panel
from devopsmind.completion.autocomplete import ensure_installed
from devopsmind.cli.runtime_registry import RUNTIME_REGISTRY

# Handlers
from devopsmind.handlers.validate_handler import handle_validate
from devopsmind.handlers.stacks_handler import handle_stacks
from devopsmind.handlers.command_handler import handle_commands
from devopsmind.handlers.ui_helpers import boxed, welcome_screen
from devopsmind.handlers.activation_handler import handle_activation_commands
from devopsmind.handlers.streak_handler import handle_streak_notification
from devopsmind.handlers.project_handler import handle_project_command
from devopsmind.programs.cli.cmd_handler import handle_program_command

# Tiers
from devopsmind.tiers.tier_migrate import migrate_foundation_core_visibility
from devopsmind.tiers.tier_migrate_paid import migrate_paid_tiers_visibility_if_active
from devopsmind.tiers.tier_update_notify import maybe_notify_tier_updates
from devopsmind.tiers.tiers import show_tiers
from devopsmind.tiers.pricing import show_pricing

# License Activation
from devopsmind.license.license_activate import activate_license
from devopsmind.license.license_upgrade import ensure_safe_foundation_state

from devopsmind.handlers.team_license_activate import (
    team_activate,
    team_status,
    team_add,
)

# 🔑 Tier ownership
from devopsmind.tiers.tier_loader import user_has_projects

# 🧭 Mentor
from devopsmind.mentor.mentor import run_mentor

# 🔐 Auth
from devopsmind.restore.auth_recovery import rotate_recovery_key

# 📖 Help
from devopsmind.help import show_help

console = Console()


# =================================================
# 🔹 CLI COMMAND REGISTRY (AUTHORITATIVE)
# =================================================
CLI_COMMANDS = [
    "introduce",
    "mentor",
    "auth",
    "logout",
    "stats",
    "doctor",
    "badges",
    "submit",
    "sync",
    "stacks",
    "mode",
    "init",
    "program",
    "programs",
]

def cancelled():
    console.print(
        Panel(
            Text("❌ Command cancelled", style="red"),
            title="Cancelled",
            border_style="red",
        )
    )
    sys.exit(0)



# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    # -------------------------------------------------
    # 🔹 Static autocomplete auto-install (idempotent)
    # -------------------------------------------------
    try:
        ensure_installed()
    except Exception:
        pass

    try:
        cmd = sys.argv[1] if len(sys.argv) > 1 else ""

        if not (len(sys.argv) >= 2 and sys.argv[1] == "login"):
            ensure_first_run()

            # 🔐 Migration guard (Foundation-safe)
            ensure_safe_foundation_state()

            # 🧩 Tier visibility migration (upgrade-safe)
            migrate_foundation_core_visibility()
            migrate_paid_tiers_visibility_if_active()

        if cmd == "login":
            ensure_first_run(force=True)
            return

        # ---------------- ARGPARSE ----------------
        parser = argparse.ArgumentParser(prog="devopsmind", add_help=False)
        parser.add_argument("--help", action="store_true")
        parser.add_argument("--version", action="store_true")

        # ✅ GLOBAL DEV FLAG
        parser.add_argument(
            "--dev",
            action="store_true",
            help="Enable developer diagnostics",
        )

        sub = parser.add_subparsers(dest="cmd")

        for c in CLI_COMMANDS:
            if c == "stacks":
                p_stacks = sub.add_parser("stacks")
                for flag in RUNTIME_REGISTRY["stacks"]["flag_map"]:
                    p_stacks.add_argument(
                        flag,
                        action="append_const",
                        const=flag,
                        dest="flags",
                    )

            elif c in ("program", "programs"):
                p = sub.add_parser(c)
                # Allow arbitrary trailing args for custom router
                p.add_argument("args", nargs=argparse.REMAINDER)

            else:
                sub.add_parser(c)


        sub.add_parser("start").add_argument("id")
        sub.add_parser("resume").add_argument("id", nargs="?")
        sub.add_parser("reset").add_argument("id")
        sub.add_parser("validate").add_argument("id")
        sub.add_parser("describe").add_argument("id")
        sub.add_parser("hint").add_argument("id")

        # ---------------- SEARCH ----------------
        p_search = sub.add_parser("search")
        p_search.add_argument("term")
        p_search.add_argument(
            "--level",
            help="Filter labs by difficulty level (case-insensitive)",
        )

        # ---------------- PROFILE ----------------
        p_profile = sub.add_parser("profile")
        profile_sub = p_profile.add_subparsers(dest="action", required=True)
        profile_sub.add_parser("show")
        profile_sub.add_parser("list")

        # ---------------- MODE ----------------
        p_mode = sub.choices["mode"]
        mode_sub = p_mode.add_subparsers(dest="action", required=True)
        mode_sub.add_parser("online")
        mode_sub.add_parser("offline")

        # ---------------- AUTH ----------------
        p_auth = sub.choices["auth"]
        auth_sub = p_auth.add_subparsers(dest="action", required=True)
        auth_sub.add_parser("rotate-recovery")

        # ---------------- PROJECTS ----------------
        sub.add_parser("projects")

        p_project = sub.add_parser("project")
        project_sub = p_project.add_subparsers(dest="subcommand")

        if user_has_projects():
            project_sub.add_parser("describe").add_argument("project_id")
            project_sub.add_parser("start").add_argument("project_id")
            project_sub.add_parser("resume").add_argument("project_id")
            project_sub.add_parser("reset").add_argument("project_id")
            project_sub.add_parser("status").add_argument("project_id")
            project_sub.add_parser("validate").add_argument("project_id")
            project_sub.add_parser("submit").add_argument("project_id")

        args = parser.parse_args()

        # -------------------------------------------------
        # 🔔 Update notification (ALL commands)
        # -------------------------------------------------
        maybe_notify_update()

        # 🧩 Tier content updates (license-aware)
        maybe_notify_tier_updates()

        maybe_notify_program_launch()

        # ---------------- STREAK NOTIFICATION ----------------
        handle_streak_notification(console)

        # ---------------- HELP ----------------
        if args.help:
            show_help()
            return

        # ---------------- VERSION ----------------
        if args.version:
            console.print(
                boxed(
                    "ℹ️ Version",
                    Text(f"DevOpsMind v{VERSION}", style="bold green"),
                )
            )
            return

        # ---------------- WELCOME ----------------
        if not args.cmd:
            console.print(boxed("👋 Welcome to DevOpsMind", welcome_screen()))
            return

        # ---------------- CORE COMMANDS ----------------
        if args.cmd == "validate":
            handle_validate(args, console, boxed)
            return

        if args.cmd == "stacks":
            flags = getattr(args, "flags", []) or []
            flag_map = RUNTIME_REGISTRY["stacks"]["flag_map"]

            # normalize / alias flags
            args.flags = [flag_map.get(f, f) for f in flags]

            handle_stacks(args, console, boxed)
            return

        # ---------------- PROJECT GUARD ----------------
        if args.cmd in ("projects", "project") and not user_has_projects():
            console.print("You don’t have any projects yet.")
            return

        # ---------------- PROJECT COMMANDS ----------------
        if args.cmd in ("projects", "project"):
            result = handle_project_command(args)
            if result:
                console.print(
                    boxed(
                        "📦 Projects",
                        result,
                    )
                )
            return

        # ---------------- PROGRAM COMMANDS ----------------
        if args.cmd in ("program", "programs"):
            handle_program_command(sys.argv[1:])
            return

        # ---------------- ACTIVATION / TEAM (GATED) ----------------
        if handle_activation_commands(args, console, boxed):
            return

        # ---------------- GENERIC COMMANDS DISPATCH ----------------
        handled = handle_commands(args, console, boxed)
        if handled:
            return

    except KeyboardInterrupt:
        cancelled()

if __name__ == "__main__":
    main()
