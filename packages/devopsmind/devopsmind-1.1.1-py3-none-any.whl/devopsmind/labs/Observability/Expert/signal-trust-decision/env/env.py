import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "OBS_CONTEXT.txt").write_text(
        "Active incident with conflicting observability signals.\n"
        "Some monitoring components may be degraded.\n"
        "Signal trust assessment required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
