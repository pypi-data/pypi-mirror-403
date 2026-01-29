import os
from pathlib import Path

WORKSPACE = Path("/workspace")
MARKER = WORKSPACE / ".devopsmind_env_done"

def seed():
    if MARKER.exists():
        return

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    os.chdir(WORKSPACE)

    (WORKSPACE / "DEGRADATION_CONTEXT.txt").write_text(
        "System operating under prolonged partial degradation.\n"
        "Reliability reduced, costs increasing.\n"
        "Executive visibility active.\n"
    )

    MARKER.write_text("done")

if __name__ == "__main__":
    seed()
