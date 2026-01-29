import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "COMMUNICATION_CONTEXT.txt").write_text(
        "High-visibility incident ongoing.\n"
        "External communication decision required.\n"
        "Executive and legal alignment needed.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
