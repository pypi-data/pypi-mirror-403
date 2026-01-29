# src/devopsmind/programs/cli/program.py

import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone

from rich.table import Table
from rich.text import Text
from rich.console import Group, Console
from rich.markdown import Markdown

from devopsmind.programs.ui import boxed_program
from devopsmind.programs.loader import load_program
from devopsmind.programs.policy_loader import load_policy, get_program_status
from devopsmind.programs.state import load_program_state
from devopsmind.programs.progress import load_progress

from devopsmind.runtime.program_container import start_program_container
from devopsmind.safety.safe_program_shell import launch_program_safe_shell
from devopsmind.programs.command_policy import get_command_policy
from devopsmind.programs.progression import compute_progress_stage

from devopsmind.programs.cert.cli import program_cert_cli

# 🔒 ADDITIVE: runtime guard (same source as labs)
from devopsmind.handlers.start_handler import (
    _fetch_required_runtime_version,
    _local_runtime_version,
    _runtime_image_exists,
)

# ✅ ADDITIVE: lifecycle helpers (NO logic duplication)
from devopsmind.programs.lifecycle import (
    resolve_program_lifecycle,
    days_until_expiry,
    days_until_launch,
)

console = Console()


def program_cli(args=None):
    if not args:
        console.print(
            boxed_program(
                "🧠 DevOpsMind Program",
                Text("Usage: devopsmind program <name>", style="dim"),
            )
        )
        return

    if args[0] == "cert":
        return program_cert_cli(args[1:])

    program = args[0]
    system = args[1] if len(args) > 1 else None

    data = load_program(program)
    if not data:
        console.print(
            boxed_program(
                "🧠 DevOpsMind Program",
                Text(f"Program '{program}' not found.", style="red"),
            )
        )
        return

    policy = load_policy(program)
    status = get_program_status(policy) if policy else "UNKNOWN"

    if status == "NOT_STARTED":
        console.print(
            boxed_program(
                f"🧠 {data['name']}",
                Text(
                    "This program is not yet available.\n\n"
                    "Please check back during its launch window.",
                    style="yellow",
                ),
            )
        )
        return

    if status == "EXPIRED":
        console.print(
            boxed_program(
                f"🧠 {data['name']}",
                Text(
                    "This program has concluded.\n\n"
                    "Thank you for your interest.",
                    style="red",
                ),
            )
        )
        return

    if system:
        body = _system_view(program, system)
        console.print(boxed_program(f"🧠 {data['name']} · {system.title()}", body))
        return

    body = _program_dashboard(data)
    console.print(boxed_program(f"🧠 {data['name']}", body))

    # -------------------------------------------------
    # 🔒 Runtime guard (IDENTICAL UX to labs)
    # -------------------------------------------------
    required = _fetch_required_runtime_version()
    local = _local_runtime_version()
    image_present = required and _runtime_image_exists(required)

    if required and not image_present:
        console.print(
            boxed_program(
                "⚠ Runtime Not Installed",
                Text(
                    "DevOpsMind runtime is not installed on this system.\n\n"
                    f"Required runtime version : {required}\n\n"
                    "Run:\n\n"
                    "  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    if not required or local != required:
        console.print(
            boxed_program(
                "⚠ Runtime Update Required",
                Text(
                    "Your DevOpsMind runtime is outdated.\n\n"
                    f"Installed version : {local or 'not installed'}\n"
                    f"Required version  : {required or 'unknown'}\n\n"
                    "Run:\n\n"
                    "  devopsmind init",
                    style="yellow",
                ),
            )
        )
        return

    _enter_program_environment(program)


# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

def _program_dashboard(data: dict):
    state = load_program_state(data["id"])
    progress = load_progress(data["id"])

    window_banner = _program_window_banner(data["id"])

    header = Group(
        Text(f"📁 Workspace: ~/workspace/programs/{data['workspace'].name}", style="dim"),
        Text(""),
        window_banner if window_banner else Text(""),
        _current_focus_banner(state),
        Text(""),
    )

    systems = _systems_table(state["systems"], progress)

    footer = Text(
        "\n▶ What next?\n"
        "  devopsmind program simulate <program>\n"
        "  devopsmind program validate <program>\n",
        style="dim",
    )

    return Group(header, systems, footer)


# ------------------------------------------------------------
# Program window banner (ADDITIVE ONLY)
# ------------------------------------------------------------

def _program_window_banner(program: str) -> Text | None:
    lifecycle = resolve_program_lifecycle(program)

    if lifecycle == "ACTIVE":
        days = days_until_expiry(program)
        if days is None:
            return None
        if days == 0:
            return Text("⏳ Program window: ends today", style="yellow")
        if days == 1:
            return Text("⏳ Program window: ends in 1 day", style="yellow")
        return Text(f"⏳ Program window: ends in {days} days", style="yellow")

    if lifecycle == "UPCOMING":
        days = days_until_launch(program)
        if days is None:
            return None
        if days == 0:
            return Text("🚀 Program launches today", style="cyan")
        if days == 1:
            return Text("🚀 Program launches tomorrow", style="cyan")
        return Text(f"🚀 Program launches in {days} days", style="cyan")

    if lifecycle == "GRACE":
        return Text("📁 Program window closed (read-only)", style="dim")

    return None


# ------------------------------------------------------------
# Guidance banner
# ------------------------------------------------------------

def _current_focus_banner(state: dict) -> Text:
    systems = state.get("systems", {})

    if systems.get("execution") != "STABILIZED":
        return Text(
            "🎯 Current Focus: Execution\n"
            "Complete Execution to unlock Resilience.\n"
            "You can explore other areas, but progress is earned in order.",
            style="cyan",
        )

    if systems.get("resilience") != "STABILIZED":
        return Text(
            "🎯 Current Focus: Resilience\n"
            "Execution is stabilized. Build Resilience to unlock Delivery.",
            style="cyan",
        )

    if systems.get("delivery") != "STABILIZED":
        return Text(
            "🎯 Current Focus: Delivery\n"
            "Finalize CI/CD and GitOps to complete the program.",
            style="cyan",
        )

    return Text(
        "🎉 All systems completed.\nYou may now submit the program.",
        style="green",
    )


# ------------------------------------------------------------
# System view
# ------------------------------------------------------------

def _system_view(program: str, system: str):
    program_root = Path(__file__).resolve().parents[1] / program
    mission_file = program_root / "missions" / f"{system}.md"

    mission = (
        Markdown(mission_file.read_text())
        if mission_file.exists()
        else Text("No mission defined.", style="red")
    )

    state = load_program_state(program)
    system_state = state["systems"].get(system, "LOCKED")

    return Group(
        Text(f"Status: {system_state}", style="yellow"),
        Text(""),
        Text("Mission", style="bold"),
        mission,
    )


# ------------------------------------------------------------
# Workspace bootstrap
# ------------------------------------------------------------

def _bootstrap_workspace_if_needed(program: str, workspace: Path):
    program_root = Path(__file__).resolve().parents[1] / program
    template_dir = program_root / "workspace_template"

    if not template_dir.exists():
        return

    for item in template_dir.iterdir():
        dest = workspace / item.name
        if dest.exists():
            continue

        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


# ------------------------------------------------------------
# Program environment
# ------------------------------------------------------------

def _enter_program_environment(program: str):
    workspace = Path.home() / "workspace" / "programs" / program
    workspace.mkdir(parents=True, exist_ok=True)

    session_file = (
        Path.home()
        / ".devopsmind"
        / "programs"
        / program
        / "session.json"
    )

    if not session_file.exists():
        _bootstrap_workspace_if_needed(program, workspace)

    if session_file.exists():
        try:
            data = json.loads(session_file.read_text())
            if subprocess.run(
                ["docker", "inspect", data["container_name"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                launch_program_safe_shell(
                    program_name=program,
                    workspace=workspace,
                    session_id=data["session_id"],
                    container_name=data["container_name"],
                )
                return
            session_file.unlink()
        except Exception:
            session_file.unlink(missing_ok=True)

    stage = compute_progress_stage(program)
    policy = get_command_policy(program, stage)

    session_id = datetime.now(timezone.utc).strftime("%H%M%S")
    container = start_program_container(
        program_name=program,
        workspace=workspace,
        program_source=Path(__file__).resolve().parents[1],
        session_id=session_id,
    )

    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(
        json.dumps(
            {
                "container_name": container,
                "session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )

    console.print(
        boxed_program(
            "▶ Entering Program Environment",
            Text(
                f"Program: {program}\n"
                "Workspace mounted and ready.\n"
                "Exit the shell to return to DevOpsMind.",
                style="green",
            ),
        )
    )

    launch_program_safe_shell(
        program_name=program,
        workspace=workspace,
        session_id=session_id,
        container_name=container,
        safety_overrides={
            "allowed_commands": policy.allowed,
            "blocked_commands": policy.blocked,
        },
    )


# ------------------------------------------------------------
# Systems table
# ------------------------------------------------------------

def _systems_table(systems_state: dict, progress: dict):
    table = Table(show_header=True, header_style="bold", box=None, expand=True)
    table.add_column("System")
    table.add_column("Status")
    table.add_column("Coverage")

    table.add_row(
        "Execution",
        _system_status_label(systems_state.get("execution")),
        _progress_summary("execution", progress),
    )
    table.add_row(
        "Resilience",
        _system_status_label(systems_state.get("resilience")),
        _progress_summary("resilience", progress),
    )
    table.add_row(
        "Delivery",
        _system_status_label(systems_state.get("delivery")),
        _progress_summary("delivery", progress),
    )

    return table


def _progress_summary(system: str, progress: dict):
    percent = int(progress.get("systems", {}).get(system, 0))
    percent = max(0, min(100, percent))

    dots = percent // 20
    return " ".join(["●"] * dots + ["○"] * (5 - dots)) + f"  {percent}%"


def _system_status_label(status: str) -> Text:
    return {
        "STABILIZED": Text("● Stabilized", style="green"),
        "IN_PROGRESS": Text("◐ In Progress", style="yellow"),
    }.get(status, Text("○ Locked", style="dim"))
