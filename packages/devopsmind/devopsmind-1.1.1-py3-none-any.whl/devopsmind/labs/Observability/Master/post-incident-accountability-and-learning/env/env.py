import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "POST_INCIDENT_CONTEXT.txt").write_text(
        "Major incident resolved.\n"
        "Post-incident review phase initiated.\n"
        "Accountability and learning decisions required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
