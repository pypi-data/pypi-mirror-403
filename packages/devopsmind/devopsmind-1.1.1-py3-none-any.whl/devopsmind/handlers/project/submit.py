# src/devopsmind/handlers/project/submit.py

"""
devopsmind project submit <project_id>

- Finalizes a validated project
- Awards PROJECT XP
- Marks project as completed (terminal)
"""

from pathlib import Path
import yaml

from rich.panel import Panel
from rich.console import Group
from rich.text import Text

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.project.describe import _available_project_ids
from devopsmind.state import load_state, save_state

DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"


def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _resolve_project_yaml(project_id: str) -> Path | None:
    for domain in LABS_DIR.iterdir():
        py = domain / "Projects" / project_id / "project.yaml"
        if py.exists():
            return py
    return None


def handle_project_submit(args):
    if not args.project_id:
        return Panel(Text("Project ID required", style="red"), border_style="red")

    project_id = canonical_id(args.project_id)

    if project_id not in _available_project_ids():
        return Panel(
            Text(f"Project '{project_id}' is not available", style="red"),
            border_style="red",
        )

    state = load_state()
    current = state.get("projects", {}).get(project_id)

    # -------------------------------------------------
    # 🔒 TERMINAL GUARD (ADDITIVE)
    # -------------------------------------------------
    if current == "completed":
        return Panel(
            Text(
                "Project already completed.\n\n"
                "Submission is final and cannot be repeated.",
                style="yellow",
            ),
            border_style="yellow",
        )

    if current != "validated":
        return Panel(
            Text(
                "Project must be validated before submission.\n\n"
                f"Current state: {current or 'not-started'}",
                style="red",
            ),
            border_style="red",
        )

    project_yaml = _resolve_project_yaml(project_id)
    if not project_yaml:
        return Panel(Text("project.yaml not found.", style="red"), border_style="red")

    meta = _load_yaml(project_yaml)
    xp = int(meta.get("xp", 0))

    xp_state = state.setdefault("xp", {})
    xp_state["projects"] = xp_state.get("projects", 0) + xp

    state.setdefault("projects", {})[project_id] = "completed"
    save_state(state)

    # -------------------------------------------------
    # 🏁 Notify project shell (AUTHORITATIVE SIGNAL)
    # -------------------------------------------------
    try:
        workspace = Path.cwd()
        (workspace / ".devopsmind_project_submitted").touch()
    except Exception:
        pass

    return Group(
        Panel(
            Text(
                f"🏁 Project submitted successfully.\n\n"
                f"Project Effort awarded: +{xp}",
                style="green",
            ),
            title="Project Completed",
            border_style="green",
        ),
        Panel(
            Text(
                "This project is complete.\n\n"
                "Explore other projects:\n"
                "  devopsmind projects\n\n"
                "Or continue with labs to progress your role.",
                style="dim",
            ),
            border_style="blue",
        ),
    )
