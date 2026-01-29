import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "INCIDENT_STATE.txt").write_text(
        "Active incident state loaded.\n"
        "User-facing impact is increasing.\n"
        "Immediate containment decisions may be required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
