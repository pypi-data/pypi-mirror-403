# src/devopsmind/programs/cli/validate.py

from pathlib import Path
import subprocess
import json
import os

from rich.console import Console, Group
from rich.text import Text

from devopsmind.programs.ui import boxed_program
from devopsmind.programs.validation import validate_workspace
from devopsmind.programs.policy_loader import load_policy, get_program_status
from devopsmind.programs.state import (
    load_program_state,
    mark_system_started,
    auto_stabilize_if_ready,
)

console = Console()
PROGRAM_SRC_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------
# Workspace enforcement
# --------------------------------------------------

def _ensure_in_workspace(program: str, workspace: Path):
    cwd = Path.cwd().resolve()
    workspace = workspace.resolve()

    if cwd == workspace or workspace in cwd.parents:
        return None

    console.print(
        boxed_program(
            "🧠 Program Validation",
            Text(
                "❌ Program validation must be run from inside the program workspace.\n\n"
                "To enter the workspace, run:\n\n"
                f"  devopsmind program {program}\n\n"
                "Then retry:\n\n"
                f"  devopsmind program validate",
                style="red",
            ),
        )
    )
    return True


# --------------------------------------------------
# CLI entry
# --------------------------------------------------

def validate_cli(args=None):
    program = args[0]

    policy = load_policy(program)
    if get_program_status(policy) != "ACTIVE":
        return

    workspace = Path.home() / "workspace" / "programs" / program
    if _ensure_in_workspace(program, workspace):
        return

    workspace_results = validate_workspace(program, workspace)
    completion_results = _run_completion_checks(program, workspace)

    body = Group(
        _render_workspace_validation(workspace_results),
        Text("\n"),
        _render_completion_readiness(program, completion_results),
    )

    console.print(boxed_program(f"🧠 Validation · {program}", body))


# ------------------------------------------------------------
# Workspace rendering (READ-ONLY)
# ------------------------------------------------------------

def _render_workspace_validation(results: list[dict]) -> Text:
    text = Text("Workspace Validation\n", style="bold")
    text.append("-" * 32 + "\n", style="dim")

    for r in results:
        if r.get("level") == "section":
            text.append(f"\n{r['message']}\n", style="bold")
            text.append("-" * 32 + "\n", style="dim")
            continue

        style = "green" if r["level"] == "ok" else "yellow"
        text.append(f"{r['symbol']} ", style=style)
        text.append(r["message"] + "\n", style="bold")

        if "why" in r:
            text.append(f"  {r['why']}\n", style="dim")
        if "suggestion" in r:
            text.append(f"  Suggestion: {r['suggestion']}\n", style="cyan")

        text.append("\n")

    return text


# ------------------------------------------------------------
# Completion checks (AUTHORITATIVE)
# ------------------------------------------------------------

def _run_completion_checks(program: str, workspace: Path) -> list[dict]:
    manifest_path = (
        PROGRAM_SRC_ROOT / "programs" / program / "checks" / "manifest.json"
    )

    manifest = json.loads(manifest_path.read_text())
    checks_dir = manifest_path.parent
    results = []

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROGRAM_SRC_ROOT.parent)  # 🔥 FIX

    for check in manifest["required"]:
        system = check["id"]
        label = check["label"]
        script = checks_dir / check["script"]

        mark_system_started(program, system)

        result = subprocess.run(
            ["python3", str(script)],
            capture_output=True,
            text=True,
            env=env,
            cwd=workspace,  # ✅ REQUIRED for correct Path resolution
        )

        if result.returncode == 0:
            auto_stabilize_if_ready(program, system)
            results.append({"label": label, "status": "pass"})
        else:
            results.append({
                "label": label,
                "status": "fail",
                "message": result.stdout.strip() or result.stderr.strip(),
            })

    return results


# ------------------------------------------------------------
# Completion rendering
# ------------------------------------------------------------

def _render_completion_readiness(program: str, results: list[dict]) -> Text:
    text = Text("Completion Status\n", style="bold")
    text.append("-" * 32 + "\n", style="dim")

    all_passed = True

    for r in results:
        if r["status"] == "pass":
            text.append("✅ ", style="green")
            text.append(r["label"] + "\n", style="bold")
        else:
            all_passed = False
            text.append("⏳ ", style="yellow")
            text.append(f"{r['label']} (Pending)\n", style="bold")

    if all_passed:
        text.append("\nAll systems completed.\n", style="green")
        text.append("\nYou may now submit the program:\n\n", style="green")
        text.append("  devopsmind program submit\n", style="bold")
    else:
        text.append(
            "\nComplete all systems above to unlock submission.\n",
            style="dim",
        )

    return text
