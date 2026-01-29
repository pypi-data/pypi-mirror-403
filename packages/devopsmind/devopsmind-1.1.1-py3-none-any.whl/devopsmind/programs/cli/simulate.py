# src/devopsmind/programs/cli/simulate.py

from pathlib import Path
from rich.text import Text
from rich.console import Console

from devopsmind.programs.ui import boxed_program
from devopsmind.programs.policy_loader import load_policy, get_program_status
from devopsmind.programs.simulation import simulate_program

console = Console()


def _ensure_in_workspace(program: str, workspace: Path):
    """
    Ensure simulate is executed from inside the program workspace.
    """
    cwd = Path.cwd().resolve()
    workspace = workspace.resolve()

    if cwd == workspace or workspace in cwd.parents:
        return None

    body = Text(
        "❌ Program simulation must be run from inside the program workspace.\n\n"
        "To enter the workspace, run:\n\n"
        f"  devopsmind program {program}\n\n"
        "Then retry:\n\n"
        f"  devopsmind program simulate",
        style="red",
    )

    console.print(boxed_program("🧠 Program Simulation", body))
    return True


def simulate_cli(args=None):
    if not args or len(args) < 1:
        body = Text(
            "Usage: devopsmind program simulate <program>",
            style="dim",
        )
        console.print(boxed_program("🧠 Program Simulation", body))
        return

    program = args[0]

    # --------------------------------------------------
    # Policy gate
    # --------------------------------------------------
    policy = load_policy(program)
    status = get_program_status(policy) if policy else "UNKNOWN"

    if status != "ACTIVE":
        body = Text(
            f"Program '{program}' is not ACTIVE.\n"
            f"Simulation is currently unavailable.",
            style="red",
        )
        console.print(boxed_program("🧠 Program Simulation", body))
        return

    # --------------------------------------------------
    # Workspace (LOCKED PATH)
    # --------------------------------------------------
    workspace = (
        Path.home()
        / "workspace"
        / "programs"
        / program
    )
    workspace.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # Workspace enforcement
    # --------------------------------------------------
    if _ensure_in_workspace(program, workspace):
        return

    # --------------------------------------------------
    # Logical simulation (NO execution)
    # --------------------------------------------------
    sim_result = simulate_program(program, workspace)

    body = Text()
    body.append(sim_result.get("summary", ""), style="bold")
    body.append("\n\n")

    if "focus" in sim_result:
        body.append("Focus areas\n", style="bold")
        body.append("-" * 32 + "\n", style="dim")
        for item in sim_result["focus"]:
            body.append(f"• {item}\n", style="cyan")
        body.append("\n")

    if "next_steps" in sim_result:
        body.append("What to do next\n", style="bold")
        body.append("-" * 32 + "\n", style="dim")
        for step in sim_result["next_steps"]:
            body.append(f"→ {step}\n", style="green")

    body.append(
        "\nThis simulation does not execute anything.\n"
        "Use validation to check your work as you progress.\n",
        style="dim",
    )

    console.print(
        boxed_program(
            f"🧠 Simulation · {program}",
            body,
        )
    )
