# src/devopsmind/programs/cli/cmd_handler.py

from rich.text import Text
from rich.console import Console

from devopsmind.programs.ui import boxed_program

from devopsmind.programs.cli.programs import programs_cli
from devopsmind.programs.cli.program import program_cli
from devopsmind.programs.cli.validate import validate_cli
from devopsmind.programs.cli.simulate import simulate_cli
from devopsmind.programs.cli.submit import handle_program_submit
from devopsmind.programs.core.consistency import check_program_consistency

console = Console()


def handle_program_command(args):
    """
    Entry point for:
      devopsmind programs
      devopsmind program <...>

    NOTE:
    - This module does NOT enforce time windows.
    - Program lifecycle is enforced per-program via lifecycle.py
    """
    if not args:
        _show_program_help()
        return

    command = args[0]

    # ---------------------------
    # devopsmind programs
    # ---------------------------
    if command == "programs":
        programs_cli(args[1:])
        return

    # ---------------------------
    # devopsmind program ...
    # ---------------------------
    if command == "program":
        _handle_program_subcommand(args[1:])
        return

    _show_program_help()


def _handle_program_subcommand(args):
    if not args:
        body = Text("Usage: devopsmind program <name>", style="dim")
        console.print(boxed_program("🧠 Program", body))
        return

    sub = args[0]

    # --------------------------------------------------
    # devopsmind program validate <program>
    # --------------------------------------------------
    if sub == "validate":
        validate_cli(args[1:])
        return

    # --------------------------------------------------
    # devopsmind program simulate <program>
    # --------------------------------------------------
    if sub == "simulate":
        simulate_cli(args[1:])
        return

    # --------------------------------------------------
    # devopsmind program submit <program>
    # --------------------------------------------------
    if sub == "submit":
        result = handle_program_submit(args[1:])
        if result:
            console.print(result)
        return

    # --------------------------------------------------
    # devopsmind program check <program>
    # --------------------------------------------------
    if sub == "check":
        if len(args) < 2:
            body = Text(
                "Usage: devopsmind program check <program>",
                style="dim",
            )
            console.print(boxed_program("🧠 Program Consistency", body))
            return

        program = args[1]
        issues = check_program_consistency(program)

        if not issues:
            console.print(
                boxed_program(
                    "✔ Program Consistency",
                    Text(
                        "All missions, validation rules, and workspace paths are aligned.",
                        style="green",
                    ),
                )
            )
        else:
            body = Text("\n".join(issues), style="yellow")
            console.print(
                boxed_program("⚠ Program Consistency Issues", body)
            )
        return

    # --------------------------------------------------
    # devopsmind program <name>
    # (dashboard / entry handled internally)
    # --------------------------------------------------
    program_cli([sub])


def _show_program_help():
    body = Text(
        "\n".join(
            [
                "Program commands:",
                "",
                "  devopsmind programs",
                "      List available programs",
                "",
                "  devopsmind program <name>",
                "      Open program dashboard or enter program environment",
                "",
                "  devopsmind program simulate <program>",
                "      View learning context and expectations",
                "",
                "  devopsmind program validate <program>",
                "      Validate workspace and receive guidance",
                "",
                "  devopsmind program submit <program>",
                "      Finalize program and clean up runtime (terminal)",
                "",
                "  devopsmind program check <program>",
                "      Check internal consistency (developer-only)",
                "",
                "  devopsmind program cert <program>",
                "      View program certificate",
            ]
        ),
        style="dim",
    )

    console.print(boxed_program("🧠 DevOpsMind Programs", body))
