import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "ORG_CONTEXT.txt").write_text(
        "Production incident affecting multiple teams.\n"
        "Escalation timing decision required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
