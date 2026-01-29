# devopsmind/handlers/activation_handler.py

from rich.text import Text


def handle_activation_commands(args, console, boxed):
    """
    Handles gated activation- and team-related commands.

    These commands are intentionally visible but disabled.
    This keeps CLI UX consistent while preventing partial activation.
    """

    # ---------------- ACTIVATE ----------------
    if args.cmd == "activate":
        console.print(
            boxed(
                "🔒 Activation",
                Text(
                    "License activation is not available in this version.\n\n"
                    "This feature is planned for a future release.\n"
                    "No action is required right now.",
                    style="yellow",
                ),
            )
        )
        return True

    # ---------------- TEAM ----------------
    if args.cmd == "team":
        action = getattr(args, "action", None)

        if action == "status":
            message = (
                "Team features are not enabled yet.\n\n"
                "Planned features include:\n"
                "• Shared licenses\n"
                "• Team progress dashboards\n"
                "• Centralized management\n"
            )

        elif action == "activate":
            message = (
                "Team license activation is not available yet.\n\n"
                "This command will be enabled in a future release."
            )

        elif action == "add":
            message = (
                "Adding team members is not supported yet.\n\n"
                "Team management features are planned post-v1."
            )

        else:
            message = (
                "Team commands are not enabled yet.\n\n"
                "This is a planned post-v1 feature."
            )

        console.print(
            boxed(
                "👥 Team",
                Text(message, style="yellow"),
            )
        )
        return True

    return False
