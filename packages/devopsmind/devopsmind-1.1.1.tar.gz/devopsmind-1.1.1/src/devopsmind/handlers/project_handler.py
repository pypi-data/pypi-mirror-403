# src/devopsmind/handlers/project_handler.py

"""
Project command router for DevOpsMind.

Supported commands:

- devopsmind projects
- devopsmind project describe <id>
- devopsmind project start <id>
- devopsmind project resume <id>
- devopsmind project validate <id>
- devopsmind project submit <id>

Lifecycle:
not-started → in-progress → validated → completed
"""

from rich.panel import Panel
from rich.text import Text

from devopsmind.tiers.tier_loader import user_has_projects

from devopsmind.handlers.project.list import handle_projects
from devopsmind.handlers.project.describe import handle_project_describe
from devopsmind.handlers.project.start import handle_project_start
from devopsmind.handlers.project.resume import handle_project_resume
from devopsmind.handlers.project.reset import handle_project_reset
from devopsmind.handlers.project.validate import handle_project_validate
from devopsmind.handlers.project.submit import handle_project_submit
from devopsmind.handlers.project.status import handle_project_status


def _projects_not_owned_panel():
    """
    Friendly, non-leaky message when user owns no projects.
    """
    return Panel(
        Text(
            "No projects available for your account.\n\n"
            "Projects are capstone missions unlocked via domain tiers.\n"
            "Install a tier or check your license to access projects.",
            style="yellow",
        ),
        title="Projects",
        border_style="yellow",
    )


def handle_project_command(args):
    """
    Route project-related commands.

    HARD RULES:
    - If user owns NO projects:
        • project commands are blocked
        • no IDs are leaked
        • friendly guidance is shown
    - Ownership is determined ONLY via tier_loader
    """

    # -------------------------------------------------
    # Ownership gate (applies to ALL project commands)
    # -------------------------------------------------
    if not user_has_projects():
        return _projects_not_owned_panel()

    # -------------------------------------------------
    # devopsmind projects
    # -------------------------------------------------
    if args.cmd == "projects":
        return handle_projects(args)

    # -------------------------------------------------
    # devopsmind project <subcommand>
    # -------------------------------------------------
    if args.cmd != "project":
        return Panel(
            Text("Invalid project command", style="red"),
            border_style="red",
        )

    sub = args.subcommand

    if sub == "describe":
        return handle_project_describe(args)

    if sub == "start":
        return handle_project_start(args)

    if sub == "resume":
        return handle_project_resume(args)

    if sub == "reset":
        return handle_project_reset(args)

    if sub == "status":
        return handle_project_status(args)

    if sub == "validate":
        return handle_project_validate(args)

    if sub == "submit":
        return handle_project_submit(args)

    return Panel(
        Text("Unknown project subcommand", style="red"),
        border_style="red",
    )
