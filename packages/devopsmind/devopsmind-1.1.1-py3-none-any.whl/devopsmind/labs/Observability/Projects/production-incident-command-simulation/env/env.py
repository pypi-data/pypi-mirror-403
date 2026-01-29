import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "INCIDENT_SIMULATION.txt").write_text(
        "Full-scale production incident simulation loaded.\n"
        "Multiple services affected.\n"
        "Executive visibility active.\n"
        "All decisions must be documented.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
