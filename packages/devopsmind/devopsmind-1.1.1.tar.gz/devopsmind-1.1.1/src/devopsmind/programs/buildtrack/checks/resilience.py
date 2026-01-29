#!/usr/bin/env python3

import sys
from pathlib import Path

from devopsmind.programs.buildtrack.validators.yaml_validator import validate_yaml_files
from devopsmind.programs.buildtrack.validators.helm_validator import validate_helm_files

from devopsmind.programs.progress import award_partial_progress, load_progress
from devopsmind.programs.state import mark_system_started, auto_stabilize_if_ready

PROGRAM_ID = "buildtrack"
SYSTEM = "resilience"
SYSTEM_TOTAL = 100

WORKSPACE = Path.home() / "workspace" / "programs" / PROGRAM_ID


def yaml_passed() -> bool:
    results = validate_yaml_files(WORKSPACE / "resilience" / "kubernetes")
    return any(r.get("level") == "ok" for r in results)


def helm_passed() -> bool:
    results = validate_helm_files(WORKSPACE / "resilience" / "helm")
    return any(r.get("level") == "ok" for r in results)


def main():
    mark_system_started(PROGRAM_ID, SYSTEM)

    if yaml_passed():
        award_partial_progress(PROGRAM_ID, SYSTEM, "yaml", 50)

    if helm_passed():
        award_partial_progress(PROGRAM_ID, SYSTEM, "helm", 50)

    progress = load_progress(PROGRAM_ID)
    if progress["systems"].get(SYSTEM, 0) >= SYSTEM_TOTAL:
        auto_stabilize_if_ready(PROGRAM_ID, SYSTEM)
        sys.exit(0)

    sys.exit(1)


if __name__ == "__main__":
    main()
