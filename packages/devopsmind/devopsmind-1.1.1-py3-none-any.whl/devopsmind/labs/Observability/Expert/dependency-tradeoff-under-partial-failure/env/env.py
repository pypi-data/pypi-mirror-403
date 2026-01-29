import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "DEPENDENCY_STATE.txt").write_text(
        "Shared dependency partially degraded.\n"
        "Some requests succeed, others fail intermittently.\n"
        "Trade-off decisions required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
