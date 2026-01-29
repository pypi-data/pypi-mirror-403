# src/devopsmind/programs/core/consistency.py

from pathlib import Path
from importlib import import_module


def check_program_consistency(program: str) -> list[str]:
    """
    Developer-only consistency checks.

    Ensures:
    - program directory exists
    - missions directory exists
    - workspace_template exists
    - validation module loads (if present)

    Does NOT enforce system-level coupling for BuildTrack.
    """

    issues = []

    program_root = Path(__file__).resolve().parents[1] / program

    if not program_root.exists():
        return [f"❌ Program directory not found: {program_root}"]

    missions_dir = program_root / "missions"
    workspace_dir = program_root / "workspace_template"

    # --------------------------------------------------
    # Structural checks
    # --------------------------------------------------
    if not missions_dir.exists():
        issues.append("❌ Missing missions/ directory")

    if not workspace_dir.exists():
        issues.append("❌ Missing workspace_template/ directory")

    # --------------------------------------------------
    # Mission sanity
    # --------------------------------------------------
    if missions_dir.exists():
        missions = list(missions_dir.glob("*.md"))
        if not missions:
            issues.append("⚠ No mission files found in missions/")

    # --------------------------------------------------
    # Validation module (optional)
    # --------------------------------------------------
    try:
        import_module(
            f"devopsmind.programs.{program}.validation"
        )
    except ModuleNotFoundError:
        issues.append("⚠ No validation module found (optional for BuildTrack)")
    except Exception as e:
        issues.append(f"❌ Validation module failed to load: {e}")

    # --------------------------------------------------
    # Workspace sanity
    # --------------------------------------------------
    if workspace_dir.exists():
        if not any(workspace_dir.iterdir()):
            issues.append("⚠ workspace_template/ is empty")

    return issues
