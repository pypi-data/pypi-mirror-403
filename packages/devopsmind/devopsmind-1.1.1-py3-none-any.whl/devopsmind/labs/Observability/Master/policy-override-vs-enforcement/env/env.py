import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "POLICY_CONTEXT.txt").write_text(
        "Critical incident ongoing.\n"
        "Policy enforcement decision required.\n"
        "Override requests submitted.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
