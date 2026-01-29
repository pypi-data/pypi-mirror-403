# devopsmind/handlers/command_handler.py

from rich.panel import Panel
from rich.text import Text

from devopsmind.help import show_help
from devopsmind.onboarding.introduce import run_introduce
from devopsmind.mentor.mentor import run_mentor
from devopsmind.restore.auth_recovery import rotate_recovery_key
from devopsmind.onboarding.mode import set_mode_online, set_mode_offline
from devopsmind.restore.sync import sync_default
from devopsmind.submit import submit_pending
from devopsmind.achievements import list_badges
from devopsmind.doctor import run_doctor
from devopsmind.stats import stats as render_stats
from devopsmind.handlers.search.search_handler import handle_search
from devopsmind.engine.describe import describe_lab
from devopsmind.engine.hint import show_hint

# ✅ RESUME HANDLER (non-destructive)
from devopsmind.handlers.resume import handle_resume

# ✅ INIT HANDLER
from devopsmind.handlers.init_handler import handle_init

# ✅ START HANDLER (single path)
from devopsmind.handlers.start_handler import handle_start

# ✅ RESET HANDLER (destructive)
from devopsmind.handlers.reset_handler import handle_reset

from devopsmind.handlers.logout_handler import confirm_and_purge_local_state
from devopsmind.onboarding.logout_ui import logout_warning_panel
from devopsmind.handlers.command_result import render_result
from devopsmind.profiles import show_profile, list_profiles



def handle_commands(args, console, boxed):
    """
    Handles all non-core commands.
    Returns True if handled.
    """

    # ---------------- HELP / VERSION ----------------
    if args.help:
        show_help()
        return True

    if args.version:
        console.print(boxed("ℹ️ Version", Text("DevOpsMind")))
        return True

    # ---------------- INIT ----------------
    if args.cmd == "init":
        handle_init()
        return True

    # ---------------- LOGOUT ----------------
    if args.cmd == "logout":
        if confirm_and_purge_local_state(console, logout_warning_panel):
            console.print(
                Panel(
                    Text(
                        "You have been logged out.\n\n"
                        "All local DevOpsMind data has been removed.\n"
                        "Run `devopsmind login` to start fresh.",
                        style="green",
                    ),
                    title="Logged Out",
                    border_style="green",
                )
            )
        return True

    # ---------------- MODE ----------------
    if args.cmd == "mode":
        set_mode_online() if args.action == "online" else set_mode_offline()
        render_result(
            console,
            boxed,
            "🔧 Mode",
            None,
            success_message=f"Mode set to {args.action}",
        )
        return True

    # ---------------- INTRODUCE ----------------
    if args.cmd == "introduce":
        run_introduce()
        return True

    # ---------------- MENTOR ----------------
    if args.cmd == "mentor":
        run_mentor()
        return True

    # ---------------- AUTH ----------------
    if args.cmd == "auth" and args.action == "rotate-recovery":
        rotate_recovery_key()
        return True

    # ---------------- SEARCH ----------------
    if args.cmd == "search":
        handle_search(args, console, boxed)
        return True

    # ---------------- START ----------------
    if args.cmd == "start":
        handle_start(args, console)
        return True

    # ---------------- RESUME ----------------
    if args.cmd == "resume":
        handle_resume(args, console)
        return True

    # ---------------- RESET ----------------
    if args.cmd == "reset":
        handle_reset(args, console)
        return True

    # ---------------- DESCRIBE ----------------
    if args.cmd == "describe":
        render_result(
            console,
            boxed,
            f"📖 Describe · {args.id}",
            describe_lab(args.id),
        )
        return True

    # ---------------- HINT ----------------
    if args.cmd == "hint":
        render_result(
            console,
            boxed,
            f"💡 Hint · {args.id}",
            show_hint(args.id),
        )
        return True

    # ---------------- STATS ----------------
    if args.cmd == "stats":
        console.print(boxed("📊 Stats", render_stats()))
        return True

    # ---------------- BADGES ----------------
    if args.cmd == "badges":
        render_result(
            console,
            boxed,
            "🏅 Badges",
            list_badges(),
        )
        return True

    # ---------------- DOCTOR ----------------
    if args.cmd == "doctor":
        render_result(
            console,
            boxed,
            "🩺 Doctor",
            run_doctor(dev=getattr(args, "dev", False)),
        )
        return True

    # ---------------- SYNC ----------------
    if args.cmd == "sync":
        render_result(
            console,
            boxed,
            "🔄 Sync",
            sync_default(),
            success_message="✅ Sync completed",
        )
        return True

    # ---------------- SUBMIT ----------------
    if args.cmd == "submit":
        render_result(
            console,
            boxed,
            "📤 Submit",
            submit_pending(),
            success_message="✅ Submission complete",
        )
        return True

    # ---------------- PROFILE ----------------
    if args.cmd == "profile":
        if args.action == "show":
            console.print(boxed("👤 Profile", show_profile()))
            return True

        if args.action == "list":
            console.print(boxed("👤 Profiles", list_profiles()))
            return True

    return False
