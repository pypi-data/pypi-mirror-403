import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "STATE.txt").write_text(
        "System state loaded.\n"
        "Multiple metrics were captured during a production incident.\n"
        "No commands are required for this lab.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
