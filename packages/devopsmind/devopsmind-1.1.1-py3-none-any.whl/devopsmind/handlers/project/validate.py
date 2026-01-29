# src/devopsmind/handlers/project/validate.py

"""
devopsmind project validate <project_id>

- Ensures required artifacts exist
- Executes project-local validator.py
- Aggregates ALL failures across files
- Marks project as validated
- Does NOT submit or award XP
"""

from pathlib import Path
import importlib.util
import yaml
import os
import uuid

from rich.panel import Panel
from rich.console import Group
from rich.text import Text

from devopsmind.handlers.id_normalizer import canonical_id
from devopsmind.handlers.project.describe import _available_project_ids
from devopsmind.state import load_state, save_state

DEVOPSMIND_ROOT = Path(__file__).resolve().parents[2]
LABS_DIR = DEVOPSMIND_ROOT / "labs"

WORKSPACE_ROOT = Path.home() / "workspace" / "project"


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def _resolve_project_dir(project_id: str) -> Path | None:
    for domain in LABS_DIR.iterdir():
        p = domain / "Projects" / project_id
        if p.exists():
            return p
    return None


def _load_validator(validator_path: Path):
    """
    Load validator.py fresh every run (no caching).
    """
    module_name = f"project_validator_{uuid.uuid4().hex}"

    spec = importlib.util.spec_from_file_location(
        module_name,
        validator_path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "validate"):
        raise RuntimeError("validator.py must define validate()")

    return module.validate


def _is_template_only(content: str) -> bool:
    """
    Detect untouched template placeholders.
    Precision-based, not character count.
    """
    markers = [
        "(describe",
        "(state",
        "(identify",
        "(document",
        "(explain",
        "(summarize",
    ]
    lowered = content.lower()
    return any(m in lowered for m in markers)


# -------------------------------------------------
# Command Handler
# -------------------------------------------------
def handle_project_validate(args):
    if not args.project_id:
        return Panel(Text("Project ID required.", style="red"), border_style="red")

    project_id = canonical_id(args.project_id)

    # -------------------------------------------------
    # Availability gate
    # -------------------------------------------------
    if project_id not in _available_project_ids():
        return Panel(
            Text(f"Project '{project_id}' is not available", style="red"),
            border_style="red",
        )

    # -------------------------------------------------
    # State gate
    # -------------------------------------------------
    state = load_state()
    current = state.get("projects", {}).get(project_id)

    if current != "in-progress":
        return Panel(
            Text(
                "Project must be in progress before validation.\n\n"
                f"Current state: {current}",
                style="red",
            ),
            border_style="red",
        )

    # -------------------------------------------------
    # Workspace check
    # -------------------------------------------------
    workspace = WORKSPACE_ROOT / project_id
    if not workspace.exists():
        return Panel(Text("Workspace not found.", style="red"), border_style="red")

    # -------------------------------------------------
    # Project definition
    # -------------------------------------------------
    project_dir = _resolve_project_dir(project_id)
    if not project_dir:
        return Panel(Text("Project definition not found.", style="red"), border_style="red")

    meta = _load_yaml(project_dir / "project.yaml")
    required = meta.get("artifacts", {}).get("required", [])
    skills = meta.get("skills", [])

    failures: list[str] = []

    # -------------------------------------------------
    # Artifact existence + template checks
    # -------------------------------------------------
    for artifact in required:
        path = workspace / artifact
        if not path.exists():
            failures.append(f"• {artifact}\n  - File missing")
            continue

        content = path.read_text(errors="ignore")
        if _is_template_only(content):
            failures.append(f"• {artifact}\n  - Template text not replaced")

    if failures:
        return Panel(
            Text(
                "❌ Project validation failed:\n\n" + "\n".join(failures),
                style="red",
            ),
            border_style="red",
        )

    # -------------------------------------------------
    # Validator execution (semantic validation)
    # -------------------------------------------------
    validator_path = project_dir / meta.get("validator", "validator.py")
    if not validator_path.exists():
        return Panel(Text("validator.py not found.", style="red"), border_style="red")

    validate_fn = _load_validator(validator_path)

    cwd = os.getcwd()
    os.chdir(workspace)
    try:
        ok, message = validate_fn()
    finally:
        os.chdir(cwd)

    if not ok:
        return Panel(
            Text(f"❌ Project validation failed:\n\n{message}", style="red"),
            border_style="red",
        )

    # -------------------------------------------------
    # State transition → validated
    # -------------------------------------------------
    state.setdefault("projects", {})[project_id] = "validated"
    save_state(state)

    # -------------------------------------------------
    # 🎓 Skills display
    # -------------------------------------------------
    skills_block = ""
    if skills:
        skills_block = (
            "\n\n🎓 Skills demonstrated:\n"
            + "\n".join(f"• {s}" for s in skills)
        )

    return Group(
        Panel(
            Text(
                "✅ Project validated successfully.\n\n"
                + message
                + skills_block,
                style="green",
            ),
            title="Validation Passed",
            border_style="green",
        ),
        Panel(
            Text(
                "Next step:\n"
                f"Submit the project to finalize and earn Effort Score:\n"
                f"  devopsmind project submit {project_id}\n\n"
                "⚠ Submission is final.",
                style="dim",
            ),
            border_style="blue",
        ),
    )
