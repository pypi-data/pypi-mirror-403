import os
import subprocess
from pathlib import Path

# -------------------------------------------------
# CONSTANTS (LOCKED)
# -------------------------------------------------
WORKSPACE_ROOT = Path("/workspace")
MARKER = WORKSPACE_ROOT / ".devopsmind_env_done"
SEED_FILE = WORKSPACE_ROOT / ".devopsmind_seed_commit"


def run(cmd):
    subprocess.run(cmd, check=True)


def seed():
    # -------------------------------------------------
    # Idempotency guard (CRITICAL)
    # -------------------------------------------------
    if MARKER.exists():
        return

    # -------------------------------------------------
    # ALWAYS operate inside learner workspace
    # -------------------------------------------------
    os.chdir(WORKSPACE_ROOT)

    # -------------------------------------------------
    # Initialize repository (ONLY ONCE)
    # -------------------------------------------------
    if (WORKSPACE_ROOT / ".git").exists():
        MARKER.write_text("done")
        return

    run(["git", "init"])
    run(["git", "branch", "-m", "main"])

    # -------------------------------------------------
    # Configure git identity (container-safe)
    # -------------------------------------------------
    run(["git", "config", "--global", "user.name", "DevOpsMind"])
    run(["git", "config", "--global", "user.email", "devopsmind@local"])

    # -------------------------------------------------
    # Base commit
    # -------------------------------------------------
    with open("core.py", "w") as f:
        f.write("def core(): pass\n")

    run(["git", "add", "core.py"])
    run(["git", "commit", "-m", "Initial core implementation"])

    # -------------------------------------------------
    # Messy feature branch
    # -------------------------------------------------
    run(["git", "checkout", "-b", "feature/refactor"])

    with open("core.py", "a") as f:
        f.write("# refactor step 1\n")
    run(["git", "commit", "-am", "WIP refactor"])

    with open("core.py", "a") as f:
        f.write("# fix typo\n")
    run(["git", "commit", "-am", "Fix typo"])

    with open("core.py", "a") as f:
        f.write("# cleanup\n")
    run(["git", "commit", "-am", "Cleanup code"])

    # -------------------------------------------------
    # Return to main
    # -------------------------------------------------
    run(["git", "checkout", "main"])

    # -------------------------------------------------
    # Record seed commit fingerprint (ONE-TIME)
    # -------------------------------------------------
    seed_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    SEED_FILE.write_text(seed_commit)

    # -------------------------------------------------
    # Mark environment initialized
    # -------------------------------------------------
    MARKER.write_text("done")


if __name__ == "__main__":
    seed()
