import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "SYSTEM_MAP.txt").write_text(
        "Multi-service production system loaded.\n"
        "Incident detected in a core dependency.\n"
        "Blast radius analysis required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
