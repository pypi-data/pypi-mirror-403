# doctor.py

import platform
import shutil
import sys
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text

from devopsmind.state import load_state
from devopsmind.utils import labs_exist, data_dir_writable
from devopsmind.schema.devopsmind_lab_lint import lint_lab
from devopsmind.tiers.tier_loader import load_visible_lab_ids
from devopsmind.mentor.engine import mentor_healthcheck
from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.handlers.id_normalizer import canonical_id


# -------------------------------------------------
# Public Docker helpers (REUSED EVERYWHERE)
# -------------------------------------------------
def docker_installed() -> bool:
    return shutil.which("docker") is not None


def docker_install_hint() -> str:
    system = platform.system()

    if system == "Linux":
        return (
            "❌ Docker not installed\n"
            "Install:\n"
            "  curl -fsSL https://get.docker.com | sh\n"
            "  sudo usermod -aG docker $USER\n"
            "  newgrp docker"
        )

    if system == "Darwin":
        return (
            "❌ Docker not installed\n"
            "Install Docker Desktop:\n"
            "https://docs.docker.com/desktop/install/mac-install/"
        )

    if system == "Windows":
        return (
            "❌ Docker not installed\n"
            "Install Docker Desktop + WSL2:\n"
            "https://docs.docker.com/desktop/install/windows-install/"
        )

    return "❌ Docker not installed (unsupported OS)"


# -------------------------------------------------
# Helper: XP consistency (UNCHANGED SEMANTICALLY)
# -------------------------------------------------
def _check_xp_consistency(state) -> tuple[str, str]:
    progress = state.get("progress", {})
    completed = progress.get("completed", [])

    derived_xp = 0

    for cid in completed:
        cid = canonical_id(cid)
        lab_dir = find_lab_by_id(cid)
        if not lab_dir:
            continue

        meta_file = lab_dir / "lab.yaml"
        if not meta_file.exists():
            continue

        try:
            meta = yaml.safe_load(meta_file.read_text()) or {}
        except Exception:
            meta = {}

        derived_xp += int(meta.get("xp", 0))

    # -------------------------------------------------
    # ✅ XP schema-safe extraction (LAB XP ONLY)
    # -------------------------------------------------
    xp = state.get("xp", 0)

    if isinstance(xp, int):           # legacy
        stored_xp = xp
    elif isinstance(xp, dict):        # new schema
        stored_xp = int(xp.get("labs", 0))
    else:
        stored_xp = 0

    if stored_xp == derived_xp:
        return ("XP consistency", f"✅ OK (lab XP = {stored_xp})")

    delta = stored_xp - derived_xp
    sign = "+" if delta > 0 else ""

    return (
        "XP consistency",
        f"⚠️ Mismatch (stored {stored_xp}, expected {derived_xp}, delta {sign}{delta})",
    )


# -------------------------------------------------
# Doctor (MAIN)
# -------------------------------------------------
def run_doctor(dev: bool = False):
    """
    Perform DevOpsMind diagnostics.

    Principles:
    - Advisory only (non-blocking)
    - Offline-safe
    - Never installs anything
    - Clear fix guidance
    """

    console = Console()
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Status")

    # -------------------------------------------------
    # Core system checks
    # -------------------------------------------------
    py_ok = sys.version_info >= (3, 8)
    table.add_row("Python ≥ 3.8", "✅" if py_ok else "❌")

    table.add_row("Operating System", platform.system())
    table.add_row("Data directory writable", "✅" if data_dir_writable() else "❌")
    table.add_row("Bundled labs", "✅" if labs_exist() else "❌")
    table.add_row("git installed", "✅" if shutil.which("git") else "❌")

    # -------------------------------------------------
    # Docker check (IMPORTANT)
    # -------------------------------------------------
    if docker_installed():
        table.add_row("Docker", "✅ Installed")
    else:
        table.add_row("Docker", docker_install_hint())

    # -------------------------------------------------
    # User progress
    # -------------------------------------------------
    state = load_state()
    completed = state.get("progress", {}).get("completed", [])
    table.add_row("Completed labs", f"✅ {len(completed)} completed")

    # -------------------------------------------------
    # XP consistency
    # -------------------------------------------------
    xp_check, xp_status = _check_xp_consistency(state)
    table.add_row(xp_check, xp_status)

    # -------------------------------------------------
    # Lab diagnostics (DEV ONLY)
    # -------------------------------------------------
    issues: list[tuple[str, list[str]]] = []

    if dev:
        table.add_row("", "")
        table.add_row("🧪 Lab diagnostics", "")

        lab_root = Path(__file__).parent / "labs"
        visible_ids = load_visible_lab_ids()

        for cid in sorted(i for i in visible_ids if isinstance(i, str) and i):
            lab_path = next(lab_root.rglob(cid), None)
            if not lab_path:
                continue

            lint_issues = lint_lab(lab_path)
            if lint_issues:
                rel = lab_path.relative_to(lab_root)
                issues.append((str(rel), lint_issues))

        total_issues = sum(len(r) for _, r in issues)

        if not issues:
            table.add_row("Lab linting", "✅ No issues detected")
        else:
            table.add_row(
                "Lab linting",
                f"⚠️ {total_issues} issue{'s' if total_issues != 1 else ''} detected (advisory)",
            )

    # -------------------------------------------------
    # Mentor diagnostics
    # -------------------------------------------------
    table.add_row("", "")
    table.add_row("🧭 Mentor diagnostics", "")

    try:
        mentor_healthcheck()
        table.add_row("Mentor engine", "✅ Online")

        provider = "Rule-based"
        if state.get("ember_enabled"):
            provider = "Ember (local AI)"
        elif state.get("paid_entitlement"):
            provider = "Paid mentor"

        table.add_row("Active mentor", f"✅ {provider}")

    except Exception as e:
        table.add_row("Mentor engine", f"❌ Unavailable ({type(e).__name__})")

    # -------------------------------------------------
    # Developer-only lint details
    # -------------------------------------------------
    if dev and issues:
        console.print("\n[bold yellow]Developer lint report:[/bold yellow]\n")
        for path, reasons in issues:
            console.print(f"• [cyan]{path}[/cyan]")
            for reason in reasons:
                console.print(f"  - {reason}")
            console.print()

    return table
