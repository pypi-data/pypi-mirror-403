# src/devopsmind/programs/cli/programs.py

from pathlib import Path
from rich.table import Table
from rich.text import Text
from rich.console import Console, Group

from devopsmind.programs.ui import boxed_program
from devopsmind.programs.loader import load_program

from devopsmind.programs.lifecycle import (
    resolve_program_lifecycle,
    is_program_visible,
    is_program_executable,
    get_program_launch_month,
    days_until_launch,
    days_until_expiry,
)

console = Console()


def programs_cli(args=None):
    programs = _discover_programs()

    active = [p for p in programs if p["lifecycle"] == "ACTIVE"]
    upcoming = [p for p in programs if p["lifecycle"] == "UPCOMING"]
    grace = [p for p in programs if p["lifecycle"] == "GRACE"]

    # --------------------------------------------------
    # ACTIVE programs
    # --------------------------------------------------
    if active:
        _render_active(active)
        return

    # --------------------------------------------------
    # UPCOMING programs
    # --------------------------------------------------
    if upcoming:
        body = _render_upcoming(upcoming)
        console.print(boxed_program("🧠 DevOpsMind Programs", body))
        return

    # --------------------------------------------------
    # GRACE programs (recently expired)
    # --------------------------------------------------
    if grace:
        body = _render_grace(grace)
        console.print(boxed_program("🧠 DevOpsMind Programs", body))
        return

    # --------------------------------------------------
    # Truly empty
    # --------------------------------------------------
    console.print(
        boxed_program(
            "🧠 DevOpsMind Programs",
            Text("No programs available at this time.", style="dim"),
        )
    )


# --------------------------------------------------
# Rendering helpers
# --------------------------------------------------

def _render_active(programs: list[dict]):
    table = Table(show_header=True, header_style="bold", box=None, expand=True)
    table.add_column("Program")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Workspace")

    executable = []

    for p in programs:
        # Build ACTIVE status with expiry hint
        status = Text("🟢 ACTIVE", style="green")

        days_left = days_until_expiry(p["id"])
        if days_left is not None:
            if days_left == 0:
                status.append(" — ends today")
            elif days_left == 1:
                status.append(" — ends in: 1 day")
            else:
                status.append(f" — ends in: {days_left} days")

        table.add_row(
            p["name"],
            status,
            p["duration"],
            f"~/workspace/programs/{p['workspace'].name}",
        )

        if is_program_executable(p["id"]):
            executable.append(p["id"])

    body = [table]

    if executable:
        lines = ["\n▶ Next steps"]
        for pid in executable:
            lines.append(f"  devopsmind program {pid}")
        body.append(Text("\n".join(lines), style="dim"))

    console.print(boxed_program("🧠 DevOpsMind Programs", Group(*body)))


def _render_upcoming(programs: list[dict]) -> Text:
    lines = ["Upcoming programs\n"]

    for p in programs:
        days = days_until_launch(p["id"])
        launch_month = get_program_launch_month(p["id"])

        if days is not None:
            if days == 0:
                suffix = " — launching today"
            elif days == 1:
                suffix = " — launching tomorrow"
            else:
                suffix = f" — launching in {days} days"
        elif launch_month:
            suffix = f" — coming in {launch_month}"
        else:
            suffix = ""

        lines.append(f"• {p['name']}{suffix}")

    return Text("\n".join(lines), style="dim")


def _render_grace(programs: list[dict]) -> Text:
    lines = [
        "Recently expired programs\n",
        "These programs are no longer active but remain visible for a short time.\n",
    ]

    for p in programs:
        lines.append(f"• {p['name']} — expired")

    return Text("\n".join(lines), style="dim")


# --------------------------------------------------
# Discovery
# --------------------------------------------------

def _discover_programs():
    root = Path(__file__).parent.parent
    items = []

    for path in root.iterdir():
        if not path.is_dir():
            continue

        info = path / "program.info"
        if not info.exists():
            continue

        program_id = path.name

        if not is_program_visible(program_id):
            continue

        data = load_program(program_id)
        if not data:
            continue

        lifecycle = resolve_program_lifecycle(program_id)

        items.append(
            {
                "id": program_id,
                "name": data["name"],
                "duration": data["duration"],
                "workspace": data["workspace"],
                "lifecycle": lifecycle,
            }
        )

    return items
