# src/devopsmind/programs/loader.py

import shutil
from pathlib import Path

# ------------------------------------------------------------
# Program roots
# ------------------------------------------------------------

# Root directory where all programs live
PROGRAMS_ROOT = Path(__file__).parent

# 🔒 LOCKED workspace root
WORKSPACE_ROOT = Path.home() / "workspace" / "programs"

# 🔒 Program → workspace name mapping
WORKSPACE_NAME_MAP = {
    "buildtrack": "buildwork",
    # infrahack will map to itself by default
}

# ------------------------------------------------------------
# Completion-safe discovery API
# ------------------------------------------------------------

def list_available_programs() -> list[str]:
    """
    List available program IDs.

    Used by:
      - shell autocomplete
      - read-only program discovery

    MUST be:
      - fast
      - side-effect free
      - filesystem-only
    """
    if not PROGRAMS_ROOT.exists():
        return []

    programs = []

    for path in PROGRAMS_ROOT.iterdir():
        if not path.is_dir():
            continue

        if path.name.startswith("_"):
            continue

        if (path / "program.info").exists():
            programs.append(path.name)

    return sorted(programs)

# ------------------------------------------------------------
# Program loader (runtime)
# ------------------------------------------------------------

def load_program(program_name: str) -> dict | None:
    """
    Backend-only loader.

    - Verifies program exists
    - Reads program.info
    - Prepares workspace (program-owned template)
    - Returns structured metadata
    """
    program_dir = PROGRAMS_ROOT / program_name
    if not program_dir.exists():
        return None

    info_path = program_dir / "program.info"
    if not info_path.exists():
        return None

    info = _read_program_info(info_path)
    workspace = _prepare_workspace(program_name)

    return {
        "id": program_name,          # canonical program id
        "name": info.get("name"),
        "mode": info.get("mode"),
        "duration": info.get("duration"),
        "workspace": workspace,
        "program_root": program_dir,
    }

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _read_program_info(path: Path) -> dict:
    data = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def _prepare_workspace(program_name: str) -> Path:
    """
    Prepare workspace from the program's own template.
    """
    workspace_name = WORKSPACE_NAME_MAP.get(program_name, program_name)
    workspace = WORKSPACE_ROOT / workspace_name

    if workspace.exists():
        return workspace

    program_dir = PROGRAMS_ROOT / program_name
    template = program_dir / "workspace_template"

    if not template.exists():
        raise RuntimeError(
            f"Program '{program_name}' does not define a workspace_template/"
        )

    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, workspace)

    return workspace
