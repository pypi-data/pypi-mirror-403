from pathlib import Path
import shutil

from devopsmind.list.lab_resolver import find_lab_by_id
from devopsmind.handlers.lab_utils import load_lab_metadata
from devopsmind.runtime.lab_container import generate_session_id

WORKSPACE_DIR = Path.home() / "workspace"

EXCLUDE_NAMES = {
    "lab.yaml",
    "validator.py",
    "__pycache__",
    "description.md",
    "env",
    ".git",          # 🔒 CRITICAL
    ".gitignore",
}

PLAY_MARKER = ".devopsmind_played"


def prepare(lab_id: str):
    """
    Prepare workspace + return execution context + START UI message.

    HARD RULE:
    - This function must not start containers
    - No runtime or Docker details leak into UI
    """

    if not lab_id:
        return None, "Please provide a lab id."

    source = find_lab_by_id(lab_id)
    if not source:
        return None, f"Lab '{lab_id}' not found."

    data = load_lab_metadata(source)

    # -------------------------------------------------
    # Execution metadata (from lab.yaml)
    # -------------------------------------------------
    execution = data.get("execution") or {}
    if execution.get("runtime") != "docker":
        return (
            None,
            "❌ Unsupported execution runtime\n\n"
            "DevOpsMind runs labs only inside Docker.",
        )

    # -------------------------------------------------
    # Session context (internal only)
    # -------------------------------------------------
    session_id = generate_session_id()

    # -------------------------------------------------
    # Prepare workspace
    # -------------------------------------------------
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    dest = WORKSPACE_DIR / lab_id
    dest.mkdir(parents=True, exist_ok=True)

    for item in source.iterdir():
        if item.name in EXCLUDE_NAMES:
            continue

        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy(item, target)

    marker = dest / PLAY_MARKER
    if not marker.exists():
        marker.write_text("played")

    # -------------------------------------------------
    # Build START screen (UX-LOCKED)
    # -------------------------------------------------
    lines = []

    lines.append(f"Title: {data.get('title', lab_id)}")
    lines.append("")

    display_path = str(dest.resolve())
    home = str(Path.home())
    if display_path.startswith(home):
        display_path = "~" + display_path[len(home):]

    lines.append("📂 Workspace:")
    lines.append(display_path)
    lines.append("")

    # 🎯 Goal
    goal = data.get("goal")
    if goal:
        lines.append("🎯 Goal:")
        if isinstance(goal, list):
            lines.extend(goal)
        else:
            lines.append(goal)
        lines.append("")

    # 🧭 Mentor guidance
    mentor_before = (
        data.get("mentor", {})
        .get("guidance", {})
        .get("before")
    )

    if mentor_before:
        lines.append("🧭 Mentor tip before you start:")
        if isinstance(mentor_before, list):
            lines.extend(mentor_before)
        else:
            lines.append(mentor_before)
        lines.append("")

    lines.append("Run `devopsmind describe` for details.")
    lines.append("Run `devopsmind validate` when ready.")
    lines.append("")
    lines.append("🔒 Entering DevOpsMind Safe Shell…")

    message = "\n".join(lines)

    # -------------------------------------------------
    # Execution context (internal only)
    # -------------------------------------------------
    context = {
        "lab_id": lab_id,
        "session_id": session_id,
        "workspace": dest,
        "stack": data.get("stack"),
        "difficulty": data.get("difficulty"),
        "execution": {
            "runtime": "docker",
            "requires_execution": execution.get(
                "requires_execution", False
            ),
        },
        "safety": data.get("safety", {}) or {},
    }

    return context, message
