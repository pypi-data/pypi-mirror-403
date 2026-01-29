import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "STAKEHOLDER_CONTEXT.txt").write_text(
        "Active incident with competing stakeholder priorities.\n"
        "Engineering, business, and compliance concerns are all present.\n"
        "Decision ownership required.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
