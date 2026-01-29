# src/devopsmind/handlers/stacks_handler.py

from rich.text import Text
from devopsmind.list.stacks import show_my_stack_progress


def handle_stacks(args, console, boxed):
    """
    Render stack progress.
    Always renders output (even if no progress yet).
    """

    section = None
    flags = args.__dict__.get("flags", []) or []

    if "--corepro" in flags or "--foundation" in flags:
        section = "corepro"
    elif "--cloudops" in flags:
        section = "cloudops"
    elif "--securityops" in flags:
        section = "securityops"
    elif "--observability" in flags:
        section = "observability"
    elif "--scenarios" in flags:
        section = "scenarios"
    elif "--story" in flags:
        section = "story"
    elif "--linux-admin" in flags:
        section = "linux-admin"
    elif "--python-dev" in flags:
        section = "python-dev"

    content = show_my_stack_progress(section)

    # 🔒 ALWAYS render something
    if content is None:
        content = Text(
            "No stack progress yet.\n\n"
            "Start a lab to begin tracking stack progress.",
            style="dim",
        )

    console.print(
        boxed(
            "📦 My Stacks & Progress",
            content,
        )
    )
