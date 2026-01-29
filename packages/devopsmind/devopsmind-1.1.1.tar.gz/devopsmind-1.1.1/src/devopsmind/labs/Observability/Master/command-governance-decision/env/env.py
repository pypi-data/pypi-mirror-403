import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "INCIDENT_COMMAND_CONTEXT.txt").write_text(
        "Major incident declared.\n"
        "Incident Commander authority activated.\n"
        "Governance and communication decisions required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
