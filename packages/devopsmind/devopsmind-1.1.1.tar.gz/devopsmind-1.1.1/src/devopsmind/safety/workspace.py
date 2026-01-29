from pathlib import Path
import os

WORKSPACE_ROOT = Path.home() / "workspace"

def ensure_inside_workspace():
    cwd = Path(os.getcwd()).resolve()
    workspace = WORKSPACE_ROOT.resolve()

    try:
        cwd.relative_to(workspace)
    except ValueError:
        raise RuntimeError(
            f"Execution blocked: commands may only run inside {workspace}"
        )
