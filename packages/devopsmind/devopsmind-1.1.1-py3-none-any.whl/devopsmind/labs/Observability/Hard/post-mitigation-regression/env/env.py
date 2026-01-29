import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "RECOVERY_STATE.txt").write_text(
        "Incident mitigation applied.\n"
        "Service initially stabilized, then regressed.\n"
        "Further analysis required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
