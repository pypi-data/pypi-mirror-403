import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "INCIDENT_STATUS.txt").write_text(
        "Active production incident detected.\n"
        "User impact is increasing.\n"
        "Escalation decision pending.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
