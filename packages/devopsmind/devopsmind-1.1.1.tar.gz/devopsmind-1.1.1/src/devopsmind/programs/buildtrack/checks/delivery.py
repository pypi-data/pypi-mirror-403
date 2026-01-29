#!/usr/bin/env python3

import sys
from pathlib import Path

from devopsmind.programs.buildtrack.validators.cicd_validator import validate_cicd_files
from devopsmind.programs.buildtrack.validators.gitops_validator import validate_gitops_files

from devopsmind.programs.progress import award_partial_progress, load_progress
from devopsmind.programs.state import mark_system_started, auto_stabilize_if_ready

PROGRAM_ID = "buildtrack"
SYSTEM = "delivery"
SYSTEM_TOTAL = 100

WORKSPACE = Path.home() / "workspace" / "programs" / PROGRAM_ID


def cicd_passed() -> bool:
    results = validate_cicd_files(WORKSPACE / "delivery" / "cicd")
    return any(r.get("level") == "ok" for r in results)


def gitops_passed() -> bool:
    results = validate_gitops_files(WORKSPACE / "delivery" / "gitops")
    return any(r.get("level") == "ok" for r in results)


def main():
    mark_system_started(PROGRAM_ID, SYSTEM)

    if cicd_passed():
        award_partial_progress(PROGRAM_ID, SYSTEM, "cicd", 50)

    if gitops_passed():
        award_partial_progress(PROGRAM_ID, SYSTEM, "gitops", 50)

    progress = load_progress(PROGRAM_ID)
    if progress["systems"].get(SYSTEM, 0) >= SYSTEM_TOTAL:
        auto_stabilize_if_ready(PROGRAM_ID, SYSTEM)
        sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
