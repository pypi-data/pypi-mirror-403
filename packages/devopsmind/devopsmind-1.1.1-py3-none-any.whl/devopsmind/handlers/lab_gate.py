from pathlib import Path

import yaml
from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm

from devopsmind.handlers.ui_helpers import boxed

console = Console()

# -------------------------------------------------
# AUTHORITATIVE paths (FIXED)
# -------------------------------------------------
# lab_gate.py → handlers → devopsmind → labs
LABS_DIR = Path(__file__).resolve().parents[1] / "labs"

# -------------------------------------------------
# AUTHORITATIVE prerequisite rules (LOCKED)
# -------------------------------------------------
PREREQUISITES = {
    "Hard": ["Easy", "Medium"],
    "Expert": ["Easy", "Medium"],
    "Master": ["Easy", "Medium", "Hard", "Expert"],
    "Architect": ["Easy", "Medium", "Hard", "Expert", "Master"],
    "Principal": ["Easy", "Medium", "Hard", "Expert", "Master"],
}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _completed_labs(state: dict) -> set[str]:
    return set(state.get("progress", {}).get("completed", []))


def _resolve_stack_dir(stack: str) -> Path | None:
    if not LABS_DIR.exists():
        return None

    for d in LABS_DIR.iterdir():
        if d.is_dir() and d.name.lower() == stack.lower():
            return d

    return None


def _labs_in_level(stack: str, level: str) -> set[str]:
    stack_dir = _resolve_stack_dir(stack)
    if not stack_dir:
        return set()

    level_dir = stack_dir / level
    if not level_dir.exists():
        return set()

    ids: set[str] = set()

    for lab_yaml in level_dir.rglob("lab.yaml"):
        try:
            data = yaml.safe_load(lab_yaml.read_text())
        except Exception:
            continue

        lab_id = data.get("id") if isinstance(data, dict) else None
        if lab_id:
            ids.add(lab_id)

    return ids


def _missing_levels(state: dict, stack: str, difficulty: str) -> list[str]:
    completed = _completed_labs(state)
    required = PREREQUISITES.get(difficulty, [])
    missing: list[str] = []

    for level in required:
        labs = _labs_in_level(stack, level)

        # No labs = cannot be complete
        if not labs:
            missing.append(level)
            continue

        if not labs.issubset(completed):
            missing.append(level)

    return missing


def _pending_prerequisite_labs(
    *, state: dict, stack: str, levels: list[str]
) -> list[tuple[str, str]]:
    completed = _completed_labs(state)
    pending: list[tuple[str, str]] = []

    for level in levels:
        for lab_id in _labs_in_level(stack, level):
            if lab_id not in completed:
                pending.append((lab_id, level))

    return sorted(pending)


# -------------------------------------------------
# MAIN GATE (FINAL)
# -------------------------------------------------
def enforce_difficulty_gate(
    *, state: dict, lab_id: str, stack: str | None, difficulty: str | None
) -> bool:
    if not stack or not difficulty:
        return True

    required_levels = PREREQUISITES.get(difficulty)
    if not required_levels:
        return True

    missing_levels = _missing_levels(state, stack, difficulty)
    if not missing_levels:
        return True

    if difficulty in {"Hard", "Expert"}:
        title = "⚠ Advanced Level Lab"
        style = "yellow"
        prompt = "Continue anyway?"
        default = True
    elif difficulty == "Master":
        title = "🚨 Master Level Lab"
        style = "bold red"
        prompt = "Proceed to MASTER level lab?"
        default = False
    else:
        title = "🚨 Senior Level Lab"
        style = "bold red"
        prompt = f"Proceed to {difficulty} level lab?"
        default = False

    console.print(
        boxed(
            title,
            Text(
                f"This is a {difficulty} level DevOpsMind lab "
                f"in the {stack.upper()} stack.\n\n"
                "Missing prerequisite levels:\n\n"
                + "\n".join(f"  • {lvl}" for lvl in missing_levels),
                style=style,
            ),
        )
    )

    if not Confirm.ask(prompt, default=default):
        pending = _pending_prerequisite_labs(
            state=state,
            stack=stack,
            levels=missing_levels,
        )

        console.print(
            boxed(
                "📋 Pending Prerequisite Labs",
                Text(
                    "\n".join(f"  • {lab} ({lvl})" for lab, lvl in pending)
                    or "  • None",
                    style="cyan",
                ),
            )
        )
        return False

    return True
