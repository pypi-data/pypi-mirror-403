import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "DECISION_CONTEXT.txt").write_text(
        "Incident ongoing.\n"
        "Proposed action is irreversible or costly to undo.\n"
        "Decision ownership required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
