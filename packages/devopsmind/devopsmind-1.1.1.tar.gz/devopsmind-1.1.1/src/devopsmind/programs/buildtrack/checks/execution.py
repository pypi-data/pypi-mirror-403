from pathlib import Path
import sys

from devopsmind.programs.buildtrack.validators.shell_validator import validate_shell_scripts
from devopsmind.programs.buildtrack.validators.docker_validator import validate_dockerfile
from devopsmind.programs.buildtrack.validators.git_validator import validate_git_design

from devopsmind.programs.progress import award_partial_progress, load_progress
from devopsmind.programs.state import mark_system_started, auto_stabilize_if_ready

PROGRAM_ID = "buildtrack"
SYSTEM = "execution"
SYSTEM_TOTAL = 100  # percentage-based system


def main():
    mark_system_started(PROGRAM_ID, SYSTEM)
    base = Path.cwd() / "execution"

    # ---- Linux ----
    if any(r["level"] == "ok" for r in validate_shell_scripts(base / "linux")):
        award_partial_progress(PROGRAM_ID, SYSTEM, "linux", 34)

    # ---- Git (design-only) ----
    if any(r["level"] == "ok" for r in validate_git_design(base / "git")):
        award_partial_progress(PROGRAM_ID, SYSTEM, "git", 33)

    # ---- Docker ----
    if any(r["level"] == "ok" for r in validate_dockerfile(base / "docker")):
        award_partial_progress(PROGRAM_ID, SYSTEM, "docker", 33)

    progress = load_progress(PROGRAM_ID)

    if progress["systems"].get(SYSTEM, 0) >= SYSTEM_TOTAL:
        auto_stabilize_if_ready(PROGRAM_ID, SYSTEM)
        sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
