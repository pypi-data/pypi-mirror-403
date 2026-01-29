import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "NOTICE.txt").write_text(
        "Incident snapshot loaded.\n"
        "Some telemetry is missing due to monitoring gaps.\n"
        "Proceed with caution.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
